from datetime import datetime
import json

from flask import jsonify, request, session

from .app_state import app, config, db
from .auth import login_required, admin_required, require_ledger_access, get_current_ledger_id
from .core import CURRENCY_NAMES, get_exchange_rate
from .models import (
    AIAnalysis,
    Account,
    Budget,
    BudgetCategoryItem,
    Category,
    ExportTask,
    FileUpload,
    InviteCode,
    Ledger,
    LedgerMember,
    Loan,
    MoneyChangeLog,
    RecurringRule,
    Transaction,
    TransactionSplit,
    User,
)
from .support import filter_transactions_by_period_orm, get_balance, log_money_change


def _bool_from_payload(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() not in ('0', 'false', 'no', 'off')
    return default


def _json_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _normalize_attachments(value):
    items = _json_list(value)
    normalized = []
    for item in items[:9]:
        if isinstance(item, str):
            normalized.append({'url': item})
        elif isinstance(item, dict):
            url = (item.get('url') or item.get('path') or '').strip()
            if url:
                normalized.append({
                    'url': url,
                    'name': (item.get('name') or '').strip(),
                    'type': (item.get('type') or '').strip(),
                })
    return normalized


def _normalize_splits(value):
    splits = []
    for item in _json_list(value):
        try:
            user_id = int(item.get('user_id'))
            amount = float(item.get('amount', 0))
        except (TypeError, ValueError):
            continue
        if user_id <= 0 or amount <= 0:
            continue
        splits.append({
            'user_id': user_id,
            'username': item.get('username') or '',
            'amount': round(amount, 2),
            'share_type': item.get('share_type') or 'equal',
        })
    return splits


def _sync_transaction_splits(tx, split_details):
    if not tx.id:
        return
    TransactionSplit.query.filter_by(transaction_id=tx.id).delete()
    for item in split_details:
        db.session.add(TransactionSplit(
            transaction_id=tx.id,
            user_id=item['user_id'],
            amount=item['amount'],
            share_type=item.get('share_type') or 'equal',
        ))


def _delete_user_owned_ledgers(user_id):
    ledgers = Ledger.query.filter_by(owner_id=user_id).all()
    for ledger in ledgers:
        replacement = LedgerMember.query.filter(
            LedgerMember.ledger_id == ledger.id,
            LedgerMember.user_id != user_id
        ).order_by(LedgerMember.id.asc()).first()

        if replacement:
            ledger.owner_id = replacement.user_id
            replacement.role = 'manager'
            InviteCode.query.filter_by(created_by=user_id, ledger_id=ledger.id).delete(synchronize_session=False)
            continue

        ledger_ids = [ledger.id]
        ledger_transaction_ids = [
            row[0] for row in db.session.query(Transaction.id).filter(Transaction.ledger_id == ledger.id).all()
        ]
        ledger_budget_ids = [
            row[0] for row in db.session.query(Budget.id).filter(Budget.ledger_id == ledger.id).all()
        ]
        ledger_account_ids = [
            row[0] for row in db.session.query(Account.id).filter(Account.ledger_id == ledger.id).all()
        ]

        Transaction.query.filter(Transaction.write_off_id.in_(ledger_transaction_ids)).update(
            {
                Transaction.reimbursement_status: 'none',
                Transaction.reimbursed_amount: 0,
                Transaction.write_off_id: None,
            },
            synchronize_session=False
        )
        Transaction.query.filter(Transaction.id.in_(ledger_transaction_ids)).update(
            {Transaction.write_off_id: None},
            synchronize_session=False
        )
        BudgetCategoryItem.query.filter(BudgetCategoryItem.budget_id.in_(ledger_budget_ids)).delete(synchronize_session=False)
        MoneyChangeLog.query.filter(MoneyChangeLog.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        MoneyChangeLog.query.filter(MoneyChangeLog.account_id.in_(ledger_account_ids)).delete(synchronize_session=False)
        RecurringRule.query.filter(RecurringRule.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        Loan.query.filter(Loan.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        Budget.query.filter(Budget.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        TransactionSplit.query.filter(TransactionSplit.transaction_id.in_(ledger_transaction_ids)).delete(synchronize_session=False)
        Transaction.query.filter(Transaction.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        Account.query.filter(Account.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        InviteCode.query.filter(InviteCode.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        LedgerMember.query.filter(LedgerMember.ledger_id.in_(ledger_ids)).delete(synchronize_session=False)
        db.session.delete(ledger)


def _delete_user_related_data(user_id):
    user_transaction_ids = [
        row[0] for row in db.session.query(Transaction.id).filter(Transaction.user_id == user_id).all()
    ]
    user_budget_ids = [
        row[0] for row in db.session.query(Budget.id).filter(Budget.user_id == user_id).all()
    ]
    user_account_ids = [
        row[0] for row in db.session.query(Account.id).filter(Account.user_id == user_id).all()
    ]

    Transaction.query.filter(Transaction.write_off_id.in_(user_transaction_ids)).update(
        {
            Transaction.reimbursement_status: 'none',
            Transaction.reimbursed_amount: 0,
            Transaction.write_off_id: None,
        },
        synchronize_session=False
    )
    Transaction.query.filter(Transaction.id.in_(user_transaction_ids)).update(
        {Transaction.write_off_id: None},
        synchronize_session=False
    )
    Transaction.query.filter(Transaction.payer_user_id == user_id).update(
        {Transaction.payer_user_id: None},
        synchronize_session=False
    )

    TransactionSplit.query.filter(
        db.or_(
            TransactionSplit.user_id == user_id,
            TransactionSplit.transaction_id.in_(user_transaction_ids)
        )
    ).delete(synchronize_session=False)
    BudgetCategoryItem.query.filter(BudgetCategoryItem.budget_id.in_(user_budget_ids)).delete(synchronize_session=False)

    MoneyChangeLog.query.filter(MoneyChangeLog.user_id == user_id).delete(synchronize_session=False)
    AIAnalysis.query.filter(AIAnalysis.user_id == user_id).delete(synchronize_session=False)
    ExportTask.query.filter(ExportTask.user_id == user_id).delete(synchronize_session=False)
    FileUpload.query.filter(FileUpload.user_id == user_id).delete(synchronize_session=False)
    RecurringRule.query.filter(RecurringRule.user_id == user_id).delete(synchronize_session=False)
    Loan.query.filter(Loan.user_id == user_id).delete(synchronize_session=False)
    Budget.query.filter(Budget.user_id == user_id).delete(synchronize_session=False)
    Transaction.query.filter(Transaction.user_id == user_id).delete(synchronize_session=False)

    MoneyChangeLog.query.filter(MoneyChangeLog.account_id.in_(user_account_ids)).delete(synchronize_session=False)
    RecurringRule.query.filter(RecurringRule.account_id.in_(user_account_ids)).update(
        {RecurringRule.account_id: None},
        synchronize_session=False
    )
    Budget.query.filter(Budget.account_id.in_(user_account_ids)).update(
        {Budget.account_id: None},
        synchronize_session=False
    )
    Transaction.query.filter(Transaction.account_id.in_(user_account_ids)).update(
        {Transaction.account_id: None},
        synchronize_session=False
    )
    Transaction.query.filter(Transaction.target_account_id.in_(user_account_ids)).update(
        {Transaction.target_account_id: None},
        synchronize_session=False
    )
    Account.query.filter(Account.user_id == user_id).delete(synchronize_session=False)

    InviteCode.query.filter(InviteCode.created_by == user_id).delete(synchronize_session=False)
    _delete_user_owned_ledgers(user_id)
    LedgerMember.query.filter(LedgerMember.user_id == user_id).delete(synchronize_session=False)


def _apply_transaction_extras(tx, payload, default_include=True):
    business_type = payload.get('business_type') or tx.business_type or 'normal'
    if business_type not in ('normal', 'transfer', 'prepay'):
        business_type = 'normal'
    tx.business_type = business_type

    if 'include_in_stats' in payload:
        tx.include_in_stats = _bool_from_payload(payload.get('include_in_stats'), default_include)
    elif tx.include_in_stats is None:
        tx.include_in_stats = default_include

    if 'location_name' in payload:
        tx.location_name = (payload.get('location_name') or '').strip() or None
    if 'latitude' in payload:
        try:
            tx.latitude = float(payload.get('latitude')) if payload.get('latitude') not in (None, '') else None
        except (TypeError, ValueError):
            tx.latitude = None
    if 'longitude' in payload:
        try:
            tx.longitude = float(payload.get('longitude')) if payload.get('longitude') not in (None, '') else None
        except (TypeError, ValueError):
            tx.longitude = None
    if 'attachments' in payload:
        attachments = _normalize_attachments(payload.get('attachments'))
        tx.attachments = json.dumps(attachments, ensure_ascii=False) if attachments else None


def _apply_account_effect(tx):
    amount = float(tx.amount or 0)
    account = Account.query.get(tx.account_id) if tx.account_id else None
    if account:
        if tx.type == 'income':
            account.balance = float(account.balance) + amount
        else:
            account.balance = float(account.balance) - amount
    if (tx.business_type or 'normal') == 'transfer' and tx.target_account_id:
        target = Account.query.get(tx.target_account_id)
        if target:
            target.balance = float(target.balance) + amount


def _rollback_account_effect(tx):
    amount = float(tx.amount or 0)
    account = Account.query.get(tx.account_id) if tx.account_id else None
    if account:
        if tx.type == 'income':
            account.balance = float(account.balance) - amount
        else:
            account.balance = float(account.balance) + amount
    if (tx.business_type or 'normal') == 'transfer' and tx.target_account_id:
        target = Account.query.get(tx.target_account_id)
        if target:
            target.balance = float(target.balance) - amount


def _rollback_account_snapshot(account_id, target_account_id, business_type, tx_type, amount):
    account = Account.query.get(account_id) if account_id else None
    if account:
        if tx_type == 'income':
            account.balance = float(account.balance) - amount
        else:
            account.balance = float(account.balance) + amount
    if (business_type or 'normal') == 'transfer' and target_account_id:
        target = Account.query.get(target_account_id)
        if target:
            target.balance = float(target.balance) - amount


def serialize_transaction(tx):
    split_details = _json_list(tx.split_details)
    try:
        split_items = tx.split_items.all()
        if split_items:
            split_details = [
                {
                    'user_id': item.user_id,
                    'username': item.user.username if item.user else '',
                    'amount': float(item.amount or 0),
                    'share_type': item.share_type or 'equal',
                    'is_settled': bool(item.is_settled),
                }
                for item in split_items
            ]
    except Exception:
        pass

    return {
        "id": tx.id,
        "type": tx.type,
        "business_type": tx.business_type or 'normal',
        "amount": float(tx.amount) if tx.amount else 0,
        "category": tx.category,
        "date": tx.date,
        "time": tx.time,
        "remark": tx.remark,
        "account_id": tx.account_id,
        "account_name": tx.account.name if tx.account else None,
        "target_account_id": tx.target_account_id,
        "target_account_name": tx.target_account.name if tx.target_account else None,
        "currency": tx.currency or 'CNY',
        "original_amount": float(tx.original_amount) if tx.original_amount else None,
        "exchange_rate": float(tx.exchange_rate) if tx.exchange_rate else None,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        "reimbursement_status": tx.reimbursement_status or 'none',
        "reimbursed_amount": float(tx.reimbursed_amount) if tx.reimbursed_amount else 0,
        "write_off_id": tx.write_off_id,
        "ledger_id": tx.ledger_id,
        "user_id": tx.user_id,
        "username": tx.user.username if tx.user else None,
        "payer_user_id": tx.payer_user_id,
        "payer_username": tx.payer_user.username if tx.payer_user else None,
        "split_details": split_details,
        "include_in_stats": bool(tx.include_in_stats if tx.include_in_stats is not None else True),
        "location_name": tx.location_name or '',
        "latitude": float(tx.latitude) if tx.latitude is not None else None,
        "longitude": float(tx.longitude) if tx.longitude is not None else None,
        "attachments": _json_list(tx.attachments),
    }


@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def get_transaction_detail(transaction_id):
    tx = Transaction.query.get(transaction_id)
    if not tx:
        return jsonify({"success": False, "message": "未找到对应交易记录"}), 404

    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    self_view = session.get('self_view', False)
    if not (is_admin and not self_view):
        if tx.ledger_id:
            has_access, role, error = require_ledger_access(tx.ledger_id, 'viewer')
            if not has_access:
                return error
        elif tx.user_id != user_id:
            return jsonify({"success": False, "message": "无权限查看此记录"}), 403

    return jsonify({"success": True, "transaction": serialize_transaction(tx)})

@app.route('/api/transactions', methods=['GET', 'POST'])
@login_required
def handle_transactions():
    # 管理员只能查看，不能创建交易（self_view 模式下允许记账）
    if request.method == 'POST' and session.get('is_admin') and not session.get('self_view'):
        return jsonify({"success": False, "message": "管理员只能查看数据，不能记账"}), 403

    if request.method == 'GET':
        limit = request.args.get('limit', config.MAX_TRANSACTIONS_DISPLAY, type=int)
        period = request.args.get('period', None)
        date = request.args.get('date', None)
        account_id = request.args.get('account_id', None, type=int)
        page = request.args.get('page', None, type=int)
        per_page = request.args.get('per_page', 8, type=int)
        # 搜索筛选参数
        keyword = request.args.get('keyword', None)
        category = request.args.get('category', None)
        tx_type = request.args.get('type', None)
        amount_min = request.args.get('amount_min', None, type=float)
        amount_max = request.args.get('amount_max', None, type=float)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        transactions_query = filter_transactions_by_period_orm(period, date)
        if account_id:
            transactions_query = transactions_query.filter_by(account_id=account_id)
        if keyword:
            like_pattern = f'%{keyword}%'
            transactions_query = transactions_query.filter(
                db.or_(Transaction.remark.like(like_pattern), Transaction.category.like(like_pattern))
            )
        if category:
            transactions_query = transactions_query.filter(Transaction.category == category)
        if tx_type in ('income', 'expense'):
            transactions_query = transactions_query.filter(Transaction.type == tx_type)
        if amount_min is not None:
            transactions_query = transactions_query.filter(Transaction.amount >= amount_min)
        if amount_max is not None:
            transactions_query = transactions_query.filter(Transaction.amount <= amount_max)
        if start_date:
            transactions_query = transactions_query.filter(Transaction.date >= start_date)
        if end_date:
            transactions_query = transactions_query.filter(Transaction.date <= end_date)

        if page is not None:
            pagination = transactions_query.paginate(page=page, per_page=per_page, error_out=False)
            transactions = pagination.items
            # 确保总数统计也遵循权限过滤
            current_ledger_id = get_current_ledger_id()
            if current_ledger_id:
                total = Transaction.query.filter(Transaction.ledger_id == current_ledger_id).count()
            else:
                user_id = session.get('user_id')
                is_admin = session.get('is_admin')
                self_view = session.get('self_view', False)
                if user_id and is_admin and not self_view:
                    total = Transaction.query.count()
                elif user_id:
                    total = Transaction.query.filter(Transaction.user_id == user_id, Transaction.ledger_id.is_(None)).count()
                else:
                    total = 0
            total_pages = pagination.pages
        else:
            transactions = transactions_query.limit(limit).all()
            # 总数也要遵循权限过滤
            current_ledger_id = get_current_ledger_id()
            if current_ledger_id:
                total = Transaction.query.filter(Transaction.ledger_id == current_ledger_id).count()
            else:
                user_id = session.get('user_id')
                is_admin = session.get('is_admin')
                self_view = session.get('self_view', False)
                if user_id and is_admin and not self_view:
                    total = Transaction.query.count()
                elif user_id:
                    total = Transaction.query.filter(Transaction.user_id == user_id, Transaction.ledger_id.is_(None)).count()
                else:
                    total = 0
            total_pages = 1

        balance = get_balance()
        return jsonify({
            "success": True,
            "transactions": [serialize_transaction(t) for t in transactions],
            "balance": balance,
            "total": total,
            "page": page or 1,
            "per_page": per_page,
            "total_pages": total_pages
        })
    elif request.method == 'POST':
        try:
            transaction = request.get_json()
            user_id = session.get('user_id')

            # 检查用户在当前账本中是否有编辑权限
            current_ledger_id = get_current_ledger_id()
            if current_ledger_id:
                has_access, role, error = require_ledger_access(current_ledger_id, 'editor')
                if not has_access:
                    return error

            # 字段校验
            business_type = transaction.get('business_type') or 'normal'
            if business_type not in ('normal', 'transfer', 'prepay'):
                business_type = 'normal'

            tx_type = transaction.get('type')
            if business_type in ('transfer', 'prepay'):
                tx_type = 'expense'
            if tx_type not in ['income', 'expense']:
                return jsonify({"success": False, "message": "交易类型必须是 income 或 expense"}), 400

            # 金额校验
            try:
                original_amount = float(transaction.get('amount', 0))
                if original_amount <= 0:
                    return jsonify({"success": False, "message": "金额必须大于0"}), 400
                if original_amount > 99999999.99:
                    return jsonify({"success": False, "message": "金额超出限制"}), 400
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "金额格式不正确"}), 400

            # 币种处理
            currency = transaction.get('currency', 'CNY').upper()
            if currency not in CURRENCY_NAMES and currency != 'CNY':
                return jsonify({"success": False, "message": f"不支持的币种: {currency}"}), 400

            exchange_rate = None
            tx_amount = original_amount
            tx_original_amount = None

            if currency == 'CNY':
                tx_amount = original_amount
            else:
                tx_original_amount = original_amount
                rate = get_exchange_rate(currency, 'CNY')
                if rate is None:
                    return jsonify({
                        "success": False,
                        "message": f"获取 {currency} 汇率失败，请稍后重试或使用人民币记账"
                    }), 502
                exchange_rate = round(rate, 6)
                tx_amount = round(original_amount * rate, 2)
                if tx_amount > 99999999.99:
                    return jsonify({"success": False, "message": "换算后金额超出限制"}), 400

            # 分类校验
            category_name = transaction.get('category', '').strip()
            if business_type == 'transfer' and not category_name:
                category_name = '转账'
            if business_type == 'prepay' and not category_name:
                category_name = '预交款'
            if not category_name:
                return jsonify({"success": False, "message": "分类不能为空"}), 400
            category = Category.query.filter_by(name=category_name, type=tx_type).first()
            if not category and business_type == 'normal':
                return jsonify({"success": False, "message": f"分类 '{category_name}' 不存在或类型不匹配"}), 400

            # 日期校验
            tx_date = transaction.get('date', '').strip()
            now = datetime.now()
            if not tx_date:
                tx_date = now.strftime('%Y-%m-%d')
            else:
                try:
                    parsed_date = datetime.strptime(tx_date, '%Y-%m-%d')
                    if parsed_date.date() > now.date():
                        return jsonify({"success": False, "message": "日期不能晚于今天"}), 400
                except ValueError:
                    return jsonify({"success": False, "message": "日期格式不正确，应为 YYYY-MM-DD"}), 400

            # 时间校验
            tx_time = transaction.get('time', '').strip()
            if not tx_time:
                tx_time = now.strftime('%H:%M:%S')
            else:
                try:
                    datetime.strptime(tx_time, '%H:%M:%S')
                except ValueError:
                    try:
                        datetime.strptime(tx_time, '%H:%M')
                        tx_time = tx_time + ':00'
                    except ValueError:
                        tx_time = now.strftime('%H:%M:%S')

            # 账户校验
            account_id = transaction.get('account_id')
            account = None
            current_ledger_id = get_current_ledger_id()
            if account_id:
                account = Account.query.filter_by(id=account_id).first()
                if (
                    not account
                    or (current_ledger_id and account.ledger_id != current_ledger_id)
                    or (not current_ledger_id and (account.user_id != user_id or account.ledger_id is not None))
                ):
                    return jsonify({"success": False, "message": "账户不存在或不属于当前账本"}), 400
            else:
                if current_ledger_id:
                    account = Account.query.filter_by(ledger_id=current_ledger_id).first()
                else:
                    account = Account.query.filter_by(user_id=user_id, ledger_id=None).first()
                if not account:
                    account = Account(name='默认账户', balance=0, account_type='cash', user_id=user_id, ledger_id=current_ledger_id)
                    db.session.add(account)
                    db.session.flush()
                account_id = account.id

            target_account_id = transaction.get('target_account_id')
            if business_type == 'transfer':
                try:
                    target_account_id = int(target_account_id)
                except (TypeError, ValueError):
                    return jsonify({"success": False, "message": "转账必须选择转入账户"}), 400
                if target_account_id == account_id:
                    return jsonify({"success": False, "message": "转入账户不能与转出账户相同"}), 400
                target_account = Account.query.filter_by(id=target_account_id).first()
                if (
                    not target_account
                    or (current_ledger_id and target_account.ledger_id != current_ledger_id)
                    or (not current_ledger_id and (target_account.user_id != user_id or target_account.ledger_id is not None))
                ):
                    return jsonify({"success": False, "message": "转入账户不存在或不属于当前账本"}), 400
            else:
                target_account_id = None

            # 创建交易记录
            split_details = _normalize_splits(transaction.get('split_details'))
            include_default = business_type == 'normal'
            tx = Transaction(
                type=tx_type,
                amount=tx_amount,
                category=category_name,
                date=tx_date,
                time=tx_time,
                remark=transaction.get('remark', '').strip(),
                account_id=account_id,
                user_id=user_id,
                ledger_id=current_ledger_id,
                currency=currency,
                original_amount=tx_original_amount,
                exchange_rate=exchange_rate,
                reimbursement_status=transaction.get('reimbursement_status', 'none'),
                payer_user_id=transaction.get('payer_user_id'),
                split_details=json.dumps(split_details, ensure_ascii=False) if split_details else None,
                business_type=business_type,
                target_account_id=target_account_id,
                include_in_stats=_bool_from_payload(transaction.get('include_in_stats'), include_default),
            )
            _apply_transaction_extras(tx, transaction, default_include=include_default)
            db.session.add(tx)

            _apply_account_effect(tx)
            db.session.flush()
            _sync_transaction_splits(tx, split_details)

            # 记录资金变动
            balance_before = float(account.balance) - (tx_amount if tx_type == 'income' else -tx_amount)
            log_money_change(
                user_id=user_id,
                action_type='create',
                entity_type='transaction',
                entity_id=tx.id,
                amount_change=tx_amount if tx_type == 'income' else -tx_amount,
                balance_before=balance_before,
                balance_after=float(account.balance),
                account_id=account_id,
                ledger_id=current_ledger_id,
                description=f'创建{business_type if business_type != "normal" else ("收入" if tx_type == "income" else "支出")} ￥{tx_amount:.2f} - {category_name}'
            )

            db.session.commit()

            balance = get_balance()
            app.logger.info(f"新增交易: {tx_type} ￥{tx_amount} - {category_name}, 账户余额: {account.balance}")

            # 支出时检查预算
            budget_warnings = []
            if tx_type == 'expense' and bool(tx.include_in_stats):
                try:
                    month = tx_date[:7]
                    # 优先查找账户级预算，再查总账户预算
                    budget_filter = {'user_id': user_id, 'month': month}
                    if current_ledger_id:
                        budget_filter['ledger_id'] = current_ledger_id
                    else:
                        budget_filter['ledger_id'] = None
                    if account_id:
                        budget_filter['account_id'] = account_id
                        budget = Budget.query.filter_by(**budget_filter).first()
                    if not budget:
                        budget_filter.pop('account_id', None)
                        budget_filter['account_id'] = None
                        budget = Budget.query.filter_by(**budget_filter).first()
                    else:
                        budget = Budget.query.filter_by(**budget_filter).first()

                    if budget:
                        total_amount = float(budget.total_amount)
                        expense_filter = [
                            Transaction.type == 'expense',
                            Transaction.date.startswith(month),
                            db.or_(Transaction.include_in_stats == True, Transaction.include_in_stats.is_(None))
                        ]
                        if current_ledger_id:
                            expense_filter.append(Transaction.ledger_id == current_ledger_id)
                        else:
                            expense_filter.extend([Transaction.user_id == user_id, Transaction.ledger_id.is_(None)])
                        if budget.account_id:
                            expense_filter.append(Transaction.account_id == budget.account_id)
                        month_expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
                            *expense_filter
                        ).scalar() or 0
                        month_expenses = float(month_expenses)

                        # 检查总预算
                        if month_expenses > total_amount:
                            budget_warnings.append({
                                'type': 'total',
                                'message': f'本月支出 ￥{month_expenses:.2f}，已超出预算 ￥{total_amount:.2f}，超出 ￥{month_expenses - total_amount:.2f}'
                            })
                        elif month_expenses >= total_amount * 0.9:
                            budget_warnings.append({
                                'type': 'total_warn',
                                'message': f'本月支出 ￥{month_expenses:.2f}，已达预算 ￥{total_amount:.2f} 的 {month_expenses / total_amount * 100:.1f}%'
                            })

                        # 检查分类预算
                        cat_items = BudgetCategoryItem.query.filter_by(budget_id=budget.id).all()
                        for item in cat_items:
                            cat_name = item.category.name if item.category else None
                            if not cat_name or cat_name != category_name:
                                continue
                            cat_amount = float(item.amount)
                            cat_exp_filter = [
                                Transaction.type == 'expense',
                                Transaction.category == cat_name,
                                Transaction.date.startswith(month),
                                db.or_(Transaction.include_in_stats == True, Transaction.include_in_stats.is_(None))
                            ]
                            if current_ledger_id:
                                cat_exp_filter.append(Transaction.ledger_id == current_ledger_id)
                            else:
                                cat_exp_filter.extend([Transaction.user_id == user_id, Transaction.ledger_id.is_(None)])
                            if budget.account_id:
                                cat_exp_filter.append(Transaction.account_id == budget.account_id)
                            cat_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
                                *cat_exp_filter
                            ).scalar() or 0
                            cat_expense = float(cat_expense)
                            if cat_expense > cat_amount:
                                budget_warnings.append({
                                    'type': 'category',
                                    'category': cat_name,
                                    'message': f'分类「{cat_name}」本月支出 ￥{cat_expense:.2f}，已超出预算 ￥{cat_amount:.2f}'
                                })
                            elif cat_expense >= cat_amount * 0.9:
                                budget_warnings.append({
                                    'type': 'category_warn',
                                    'category': cat_name,
                                    'message': f'分类「{cat_name}」支出 ￥{cat_expense:.2f}，已达预算 ￥{cat_amount:.2f} 的 {cat_expense / cat_amount * 100:.1f}%'
                                })
                except Exception as e:
                    app.logger.warning(f"预算检查失败: {e}")

            # 报销收入关联：手动添加"报销收入"时可关联原始支出
            write_off_warning = None
            if tx_type == 'income' and category_name == '报销收入':
                linked_expense_id = transaction.get('write_off_id')
                if linked_expense_id:
                    try:
                        expense_tx = Transaction.query.get(linked_expense_id)
                        if expense_tx and expense_tx.type == 'expense' and expense_tx.reimbursement_status != 'none':
                            current_reimbursed = float(expense_tx.reimbursed_amount or 0)
                            new_total = current_reimbursed + tx_amount
                            orig_amount = float(expense_tx.amount)
                            if new_total > orig_amount:
                                write_off_warning = f'核销金额累计 {new_total:.2f} 超出原支出金额 {orig_amount:.2f}'
                            else:
                                expense_tx.reimbursed_amount = new_total
                                expense_tx.write_off_id = tx.id
                                expense_tx.reimbursement_status = 'reimbursed' if new_total >= orig_amount else 'partial'
                                expense_tx.updated_at = datetime.now()
                                db.session.commit()
                                app.logger.info(f"报销收入关联支出: income={tx.id}, expense={expense_tx.id}")
                    except Exception as e:
                        app.logger.warning(f"报销收入关联失败: {e}")
                else:
                    write_off_warning = '未关联原始支出，请前往报销管理进行核销'

            response_data = {
                "success": True,
                "message": "交易添加成功",
                "balance": balance,
                "account_balance": float(account.balance),
                "transaction_id": tx.id
            }
            if budget_warnings:
                response_data['budget_warnings'] = budget_warnings
                response_data['message'] = '交易添加成功，但存在预算超支警告'
            if write_off_warning:
                response_data['write_off_warning'] = write_off_warning
                if not response_data.get('budget_warnings'):
                    response_data['message'] = '交易添加成功，' + write_off_warning
            return jsonify(response_data), 201
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"添加交易失败: {e}")
            return jsonify({"success": False, "message": "添加交易失败"}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    try:
        tx = Transaction.query.get(transaction_id)
        if not tx:
            return jsonify({"success": False, "message": "未找到对应交易记录"}), 404

        # 检查权限：管理员在 self_view 模式下可以删除自己的交易，否则只能查看
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        if is_admin and not self_view:
            return jsonify({"success": False, "message": "管理员只能查看数据，不能删除交易"}), 403
        if tx.user_id != user_id:
            # Check if user has editor role in the transaction's ledger
            if tx.ledger_id:
                has_access, role, error = require_ledger_access(tx.ledger_id, 'editor')
                if not has_access:
                    return error
            else:
                return jsonify({"success": False, "message": "无权限删除此记录"}), 403

        # 回滚账户余额
        _rollback_account_effect(tx)

        # 处理核销关联：删除已报销的支出时同步删除关联的收入
        if tx.type == 'expense' and tx.write_off_id:
            linked_income = Transaction.query.get(tx.write_off_id)
            if linked_income:
                # 回滚关联收入的账户余额
                linked_account = Account.query.get(linked_income.account_id) if linked_income.account_id else None
                if linked_account:
                    linked_account.balance = float(linked_account.balance) - float(linked_income.amount)
                log_money_change(
                    user_id=user_id,
                    action_type='delete',
                    entity_type='transaction',
                    entity_id=linked_income.id,
                    amount_change=-float(linked_income.amount),
                    account_id=linked_income.account_id,
                    ledger_id=linked_income.ledger_id,
                    description=f'删除关联报销收入 ￥{float(linked_income.amount):.2f}'
                )
                db.session.delete(linked_income)
        # 处理核销关联：删除报销收入时重置对应支出的报销状态
        elif tx.type == 'income':
            linked_expenses = Transaction.query.filter_by(write_off_id=transaction_id).all()
            for exp in linked_expenses:
                exp.reimbursement_status = 'none'
                exp.reimbursed_amount = 0
                exp.write_off_id = None

        # 记录资金变动（主交易）
        amt_change = -float(tx.amount) if tx.type == 'income' else float(tx.amount)
        log_money_change(
            user_id=user_id,
            action_type='delete',
            entity_type='transaction',
            entity_id=transaction_id,
            amount_change=amt_change,
            account_id=tx.account_id,
            ledger_id=tx.ledger_id,
            description=f'删除{tx.business_type if (tx.business_type or "normal") != "normal" else ("收入" if tx.type == "income" else "支出")} ￥{float(tx.amount):.2f} - {tx.category}'
        )

        db.session.delete(tx)
        db.session.commit()
        balance = get_balance()
        app.logger.info(f"删除交易: ID={transaction_id}, {tx.type} ￥{tx.amount}")

        return jsonify({
            "success": True,
            "message": "记录已删除",
            "new_balance": balance
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除交易失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    try:
        update_data = request.get_json()
        tx = Transaction.query.get(transaction_id)
        if not tx:
            return jsonify({"success": False, "message": "未找到对应交易记录"}), 404

        # 检查权限：管理员在 self_view 模式下可以修改自己的交易，否则只能查看
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        if is_admin and not self_view:
            return jsonify({"success": False, "message": "管理员只能查看数据，不能修改交易"}), 403
        if tx.user_id != user_id:
            if tx.ledger_id:
                has_access, role, error = require_ledger_access(tx.ledger_id, 'editor')
                if not has_access:
                    return error
            else:
                return jsonify({"success": False, "message": "无权限修改此记录"}), 403

        # 先回滚旧的账户余额影响
        old_type = tx.type
        old_amount = float(tx.amount)
        old_business_type = tx.business_type or 'normal'
        old_account_id = tx.account_id
        old_target_account_id = tx.target_account_id

        # 更新字段
        new_business_type = update_data.get('business_type', old_business_type) or 'normal'
        if new_business_type not in ('normal', 'transfer', 'prepay'):
            new_business_type = 'normal'
        tx.business_type = new_business_type

        new_type = update_data.get('type', old_type)
        if new_business_type in ('transfer', 'prepay'):
            new_type = 'expense'
        new_amount = old_amount
        if new_type not in ['income', 'expense']:
            return jsonify({"success": False, "message": "交易类型必须是 income 或 expense"}), 400
        tx.type = new_type

        if 'amount' in update_data:
            try:
                raw_amount = float(update_data['amount'])
                if raw_amount <= 0:
                    return jsonify({"success": False, "message": "金额必须大于0"}), 400
                if raw_amount > 99999999.99:
                    return jsonify({"success": False, "message": "金额超出限制"}), 400
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "金额格式不正确"}), 400

            # 币种处理
            currency = update_data.get('currency', tx.currency or 'CNY').upper()
            if currency not in CURRENCY_NAMES and currency != 'CNY':
                return jsonify({"success": False, "message": f"不支持的币种: {currency}"}), 400

            if currency == 'CNY':
                new_amount = raw_amount
                tx.currency = 'CNY'
                tx.original_amount = None
                tx.exchange_rate = None
            else:
                rate = get_exchange_rate(currency, 'CNY')
                if rate is None:
                    return jsonify({
                        "success": False,
                        "message": f"获取 {currency} 汇率失败，请稍后重试或使用人民币记账"
                    }), 502
                new_amount = round(raw_amount * rate, 2)
                if new_amount > 99999999.99:
                    return jsonify({"success": False, "message": "换算后金额超出限制"}), 400
                tx.currency = currency
                tx.original_amount = raw_amount
                tx.exchange_rate = round(rate, 6)

            tx.amount = new_amount

        if 'category' in update_data and update_data['category']:
            category_name = update_data['category'].strip()
            category = Category.query.filter_by(name=category_name, type=new_type).first()
            if not category and new_business_type == 'normal':
                return jsonify({"success": False, "message": f"分类 '{category_name}' 不存在或类型不匹配"}), 400
            tx.category = category_name
        elif new_business_type == 'transfer':
            tx.category = tx.category or '转账'
        elif new_business_type == 'prepay':
            tx.category = tx.category or '预交款'

        if 'remark' in update_data:
            tx.remark = update_data['remark'].strip() if update_data['remark'] else ''
        if 'account_id' in update_data:
            new_account = Account.query.get(update_data['account_id'])
            if not new_account:
                return jsonify({"success": False, "message": "账户不存在"}), 400
            if tx.ledger_id and new_account.ledger_id != tx.ledger_id:
                return jsonify({"success": False, "message": "账户不属于当前账本"}), 400
            if not tx.ledger_id and not (is_admin and not self_view) and new_account.user_id != user_id:
                return jsonify({"success": False, "message": "无权限使用该账户"}), 403
            tx.account_id = update_data['account_id']

        if new_business_type == 'transfer':
            try:
                target_account_id = int(update_data.get('target_account_id') or tx.target_account_id)
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "转账必须选择转入账户"}), 400
            if target_account_id == tx.account_id:
                return jsonify({"success": False, "message": "转入账户不能与转出账户相同"}), 400
            target_account = Account.query.get(target_account_id)
            if not target_account or (tx.ledger_id and target_account.ledger_id != tx.ledger_id):
                return jsonify({"success": False, "message": "转入账户不存在或不属于当前账本"}), 400
            tx.target_account_id = target_account_id
        elif 'target_account_id' in update_data or new_business_type != 'transfer':
            tx.target_account_id = None

        if 'payer_user_id' in update_data:
            tx.payer_user_id = update_data['payer_user_id']
        if 'reimbursement_status' in update_data:
            new_status = update_data.get('reimbursement_status') or 'none'
            if new_status not in ('none', 'pending', 'partial', 'reimbursed'):
                return jsonify({"success": False, "message": "无效的报销状态"}), 400
            if new_type != 'expense':
                new_status = 'none'
            tx.reimbursement_status = new_status
        if 'split_details' in update_data:
            split_details = _normalize_splits(update_data.get('split_details'))
            tx.split_details = json.dumps(split_details, ensure_ascii=False) if split_details else None
            _sync_transaction_splits(tx, split_details)

        _apply_transaction_extras(tx, update_data, default_include=(new_business_type == 'normal'))

        tx.updated_at = datetime.now()

        # 应用新余额影响
        _rollback_account_snapshot(old_account_id, old_target_account_id, old_business_type, old_type, old_amount)
        _apply_account_effect(tx)

        # 记录资金变动
        old_effect = old_amount if old_type == 'income' else -old_amount
        new_effect = new_amount if new_type == 'income' else -new_amount
        net_change = new_effect - old_effect
        log_money_change(
            user_id=user_id,
            action_type='update',
            entity_type='transaction',
            entity_id=transaction_id,
            amount_change=net_change,
            account_id=tx.account_id,
            ledger_id=tx.ledger_id,
            description=f'更新交易: {old_business_type}/{old_type}￥{old_amount:.2f} → {new_business_type}/{new_type}￥{new_amount:.2f} - {tx.category}'
        )

        db.session.commit()
        balance = get_balance()
        app.logger.info(f"更新交易: ID={transaction_id}, {new_type} ￥{new_amount}")

        return jsonify({
            "success": True,
            "message": "记录已更新",
            "transaction": serialize_transaction(tx),
            "new_balance": balance
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新交易失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== 报销管理 API ====================

@app.route('/api/transactions/<int:transaction_id>/reimbursement', methods=['PUT'])
@login_required
def update_reimbursement(transaction_id):
    """Update reimbursement status of a transaction"""
    try:
        tx = Transaction.query.get(transaction_id)
        if not tx:
            return jsonify({"success": False, "message": "未找到对应交易记录"}), 404

        # 检查权限：管理员在 self_view 模式下可以操作报销
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        if is_admin and not self_view:
            return jsonify({"success": False, "message": "管理员只能查看数据，不能操作报销"}), 403
        if tx.user_id != user_id:
            return jsonify({"success": False, "message": "无权限修改此记录"}), 403
        if tx.type != 'expense':
            return jsonify({"success": False, "message": "只有支出记录可以标记报销"}), 400

        data = request.get_json()
        new_status = data.get('reimbursement_status')
        if new_status not in ('none', 'pending', 'partial', 'reimbursed'):
            return jsonify({"success": False, "message": "无效的报销状态"}), 400

        tx.reimbursement_status = new_status
        tx.updated_at = datetime.now()
        db.session.commit()

        app.logger.info(f"更新报销状态: transaction={transaction_id}, status={new_status}")
        return jsonify({
            "success": True,
            "message": "报销状态已更新",
            "transaction": {
                "id": tx.id,
                "reimbursement_status": tx.reimbursement_status,
                "reimbursed_amount": float(tx.reimbursed_amount) if tx.reimbursed_amount else 0,
                "write_off_id": tx.write_off_id
            }
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新报销状态失败: {e}")
        return jsonify({"success": False, "message": "更新报销状态失败"}), 500


@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def admin_reset_user_password(user_id):
    if session.get('self_view'):
        return jsonify({"success": False, "message": "请在管理后台使用该功能"}), 403

    target_user = User.query.get(user_id)
    if not target_user:
        return jsonify({"success": False, "message": "用户不存在"}), 404
    if target_user.is_admin:
        return jsonify({"success": False, "message": "管理员账号请使用自己的密码修改入口"}), 400

    data = request.get_json(silent=True) or {}
    new_password = (data.get('new_password') or '').strip()
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "新密码长度不能少于6位"}), 400

    target_user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": f"已重置用户 {target_user.username} 的密码"})


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    try:
        if session.get('self_view'):
            return jsonify({"success": False, "message": "请在管理后台使用该功能"}), 403

        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        if target_user.is_admin:
            return jsonify({"success": False, "message": "不能删除管理员账号"}), 400

        username = target_user.username
        _delete_user_related_data(target_user.id)
        db.session.delete(target_user)
        db.session.commit()
        app.logger.info(f"管理员删除用户: id={user_id}, username={username}")
        return jsonify({"success": True, "message": f"用户 {username} 已删除"})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"管理员删除用户失败: user_id={user_id}, error={e}")
        return jsonify({"success": False, "message": "删除用户失败，请检查关联数据后重试"}), 500


@app.route('/api/transactions/<int:transaction_id>/write-off', methods=['POST'])
@login_required
def create_write_off(transaction_id):
    """Create reimbursement income and link as write-off to the original expense"""
    try:
        tx = Transaction.query.get(transaction_id)
        if not tx:
            return jsonify({"success": False, "message": "未找到对应交易记录"}), 404

        # 检查权限：管理员在 self_view 模式下可以核销
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        if is_admin and not self_view:
            return jsonify({"success": False, "message": "管理员只能查看数据，不能核销报销"}), 403
        if tx.user_id != user_id:
            return jsonify({"success": False, "message": "无权限修改此记录"}), 403
        if tx.type != 'expense':
            return jsonify({"success": False, "message": "只有支出记录可以核销"}), 400
        if tx.reimbursement_status == 'none':
            return jsonify({"success": False, "message": "该记录未标记为报销，请先标记"}), 400

        data = request.get_json()
        write_off_amount = float(data.get('amount', 0))
        if write_off_amount <= 0:
            return jsonify({"success": False, "message": "核销金额必须大于0"}), 400

        original_amount = float(tx.amount)
        current_reimbursed = float(tx.reimbursed_amount or 0)
        new_total_reimbursed = current_reimbursed + write_off_amount

        if new_total_reimbursed > original_amount:
            return jsonify({
                "success": False,
                "message": f"核销金额累计 {new_total_reimbursed:.2f} 超出原支出金额 {original_amount:.2f}"
            }), 400

        # Create the reimbursement income transaction
        write_off_tx = Transaction(
            type='income',
            amount=write_off_amount,
            category='报销收入',
            date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
            time=data.get('time', datetime.now().strftime('%H:%M:%S')),
            remark=data.get('remark', f'核销报销: {tx.remark or tx.category}')[:255],
            account_id=tx.account_id,
            user_id=session.get('user_id'),
            currency='CNY',
            ledger_id=tx.ledger_id
        )
        db.session.add(write_off_tx)
        db.session.flush()

        # Update the original expense
        tx.reimbursed_amount = new_total_reimbursed
        tx.write_off_id = write_off_tx.id
        tx.reimbursement_status = 'reimbursed' if new_total_reimbursed >= original_amount else 'partial'
        tx.updated_at = datetime.now()

        # Update account balance for the reimbursement income
        account = Account.query.get(tx.account_id) if tx.account_id else None
        if account:
            account.balance = float(account.balance) + write_off_amount

        # 记录资金变动
        if account:
            balance_after = float(account.balance)
            log_money_change(
                user_id=session.get('user_id'),
                action_type='create',
                entity_type='transaction',
                entity_id=write_off_tx.id,
                amount_change=write_off_amount,
                balance_before=balance_after - write_off_amount,
                balance_after=balance_after,
                account_id=tx.account_id,
                ledger_id=tx.ledger_id,
                description=f'创建报销收入 ￥{write_off_amount:.2f} - 核销原支出 #{transaction_id}'
            )

        db.session.commit()

        app.logger.info(f"核销报销: expense={transaction_id}, amount={write_off_amount}, income={write_off_tx.id}")
        return jsonify({
            "success": True,
            "message": "核销成功",
            "write_off_transaction": {
                "id": write_off_tx.id,
                "amount": write_off_amount,
                "date": write_off_tx.date
            },
            "updated_expense": {
                "id": tx.id,
                "reimbursement_status": tx.reimbursement_status,
                "reimbursed_amount": float(tx.reimbursed_amount),
                "write_off_id": tx.write_off_id
            },
            "account_balance": float(account.balance) if account else None
        }), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"核销报销失败: {e}")
        return jsonify({"success": False, "message": "核销失败"}), 500


@app.route('/api/reimbursements', methods=['GET'])
@login_required
def list_reimbursements():
    """List expenses with reimbursement activity, with optional filtering"""
    try:
        status_filter = request.args.get('status', None)
        account_id = request.args.get('account_id', None, type=int)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)

        query = Transaction.query.filter(
            Transaction.type == 'expense',
            Transaction.reimbursement_status != 'none'
        )

        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        current_ledger_id = get_current_ledger_id()
        if current_ledger_id:
            query = query.filter(Transaction.ledger_id == current_ledger_id)
        elif user_id and not is_admin or (is_admin and self_view):
            # 普通用户或管理员 self_view 只能看到自己的数据
            query = query.filter(Transaction.user_id == user_id, Transaction.ledger_id.is_(None))

        if status_filter and status_filter != 'all':
            query = query.filter(Transaction.reimbursement_status == status_filter)
        if account_id:
            query = query.filter_by(account_id=account_id)
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)

        query = query.order_by(Transaction.id.desc())
        transactions = query.all()

        # Build response with optional write-off info
        result = []
        for t in transactions:
            item = {
                "id": t.id,
                "amount": float(t.amount),
                "category": t.category,
                "date": t.date,
                "remark": t.remark,
                "account_id": t.account_id,
                "account_name": t.account.name if t.account else None,
                "reimbursement_status": t.reimbursement_status,
                "reimbursed_amount": float(t.reimbursed_amount) if t.reimbursed_amount else 0,
                "write_off_id": t.write_off_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "user_id": t.user_id,
                "username": t.user.username if t.user else None
            }
            # Include linked write-off income info
            if t.write_off_id:
                if is_admin and not self_view:
                    # 管理员可以看到所有关联数据
                    wot = Transaction.query.get(t.write_off_id)
                    if wot:
                        item["write_off_transaction"] = {
                            "id": wot.id,
                            "amount": float(wot.amount),
                            "date": wot.date,
                            "remark": wot.remark
                        }
                else:
                    # 普通用户或管理员 self_view 只能看到自己的关联数据
                    if t.user_id == user_id:
                        wot = Transaction.query.get(t.write_off_id)
                        if wot:
                            item["write_off_transaction"] = {
                                "id": wot.id,
                                "amount": float(wot.amount),
                                "date": wot.date,
                                "remark": wot.remark
                            }
            result.append(item)

        # 统计计数（根据权限）
        def _count_with_ledger(base_filter):
            if current_ledger_id:
                return Transaction.query.filter(*base_filter, Transaction.ledger_id == current_ledger_id).count()
            if is_admin and not self_view:
                return Transaction.query.filter(*base_filter).count()
            return Transaction.query.filter(*base_filter, Transaction.user_id == user_id, Transaction.ledger_id.is_(None)).count()

        pending_count = _count_with_ledger([
            Transaction.type == 'expense',
            Transaction.reimbursement_status == 'pending'
        ])
        partial_count = _count_with_ledger([
            Transaction.type == 'expense',
            Transaction.reimbursement_status == 'partial'
        ])
        reimbursed_count = _count_with_ledger([
            Transaction.type == 'expense',
            Transaction.reimbursement_status == 'reimbursed'
        ])

        return jsonify({
            "success": True,
            "reimbursements": result,
            "total": len(result),
            "summary": {
                "total_pending": pending_count,
                "total_partial": partial_count,
                "total_reimbursed": reimbursed_count
            }
        })
    except Exception as e:
        app.logger.error(f"获取报销列表失败: {e}")
        return jsonify({"success": False, "message": "获取报销列表失败"}), 500


# ==================== 借贷管理 API ====================


