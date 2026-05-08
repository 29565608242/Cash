import json
from datetime import datetime

from flask import session

from .app_state import db
from .auth import get_current_ledger_id
from .models import Ledger, LedgerMember, MoneyChangeLog, Transaction

def get_balance():
    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    self_view = session.get('self_view', False)

    if not user_id:
        return 0

    # 管理员后台模式：查看所有用户的余额
    current_ledger_id = get_current_ledger_id()
    if is_admin and not self_view:
        income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
        expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
    elif current_ledger_id:
        income = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.ledger_id == current_ledger_id, Transaction.type == 'income'
        ).scalar() or 0
        expense = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.ledger_id == current_ledger_id, Transaction.type == 'expense'
        ).scalar() or 0
    else:
        income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='income', user_id=user_id).scalar() or 0
        expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='expense', user_id=user_id).scalar() or 0

    return float(income - expense)

def filter_transactions_by_period_orm(period=None, date=None):
    query = Transaction.query.options(db.joinedload(Transaction.user))

    now = datetime.now()

    user_id = session.get('user_id')
    is_admin = session.get('is_admin')
    self_view = session.get('self_view', False)

    # 管理员后台模式：查看所有用户的全部数据，不做任何账本/用户过滤
    if user_id and is_admin and not self_view:
        pass
    else:
        current_ledger_id = get_current_ledger_id()
        if current_ledger_id:
            query = query.filter(Transaction.ledger_id == current_ledger_id)
        elif user_id:
            query = query.filter(Transaction.user_id == user_id)

    if date:
        query = query.filter(Transaction.date == date)
    elif period == 'day':
        today = now.strftime('%Y-%m-%d')
        query = query.filter(Transaction.date == today)
    elif period == 'week':
        query = query.order_by(Transaction.date.desc()).limit(50)
    elif period == 'month':
        current_month = now.strftime('%Y-%m')
        query = query.filter(Transaction.date.startswith(current_month))
    elif period == 'year':
        current_year = now.strftime('%Y')
        query = query.filter(Transaction.date.startswith(current_year))
    return query.order_by(Transaction.id.desc())


def log_money_change(user_id, action_type, entity_type, entity_id=None, amount_change=0,
                     balance_before=None, balance_after=None, account_id=None,
                     ledger_id=None, description=None, details=None):
    """记录资金变动日志"""
    log = MoneyChangeLog(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        amount_change=amount_change,
        balance_before=balance_before,
        balance_after=balance_after,
        account_id=account_id,
        ledger_id=ledger_id,
        description=description,
        details=json.dumps(details, ensure_ascii=False) if details else None
    )
    db.session.add(log)
