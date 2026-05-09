import hashlib
import os
import secrets
import time
from datetime import datetime
from functools import wraps

from flask import Blueprint, g, jsonify, request, session
from werkzeug.utils import secure_filename

from .app_state import app, db
from .auth import get_current_ledger_id, login_required
from .models import Account, Budget, Ledger, LedgerMember, Transaction, User
from .support import get_balance

miniapp_bp = Blueprint('miniapp', __name__, url_prefix='/api/miniapp')

# 开发阶段内存 token 存储；生产建议迁移到 Redis
_tokens = {}  # {token: {'user_id': int, 'expires_at': float}}
TOKEN_EXPIRE_SECONDS = 86400 * 7


def _extract_token(auth_header):
    if not auth_header:
        return ''
    auth_header = auth_header.strip()
    if auth_header.lower().startswith('bearer '):
        return auth_header[7:].strip()
    return auth_header


def _get_request_token():
    return _extract_token(request.headers.get('Authorization', ''))


def _prune_token(token):
    info = _tokens.get(token)
    if not info:
        return None
    if info.get('expires_at', 0) <= time.time():
        _tokens.pop(token, None)
        return None
    return info


def generate_token(user_id):
    raw = f'{user_id}:{time.time()}:{secrets.token_hex(16)}:{app.config["SECRET_KEY"]}'
    token = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    _tokens[token] = {
        'user_id': user_id,
        'expires_at': time.time() + TOKEN_EXPIRE_SECONDS,
    }
    return token


def resolve_user_from_token(auth_header_or_token):
    token = _extract_token(auth_header_or_token)
    if not token:
        return None
    info = _prune_token(token)
    if not info:
        return None
    return User.query.get(info['user_id'])


def _apply_user_session(user):
    g.user = user
    session['user_id'] = user.id
    session['is_admin'] = bool(user.is_admin)
    session['self_view'] = True


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_request_token()
        if not token:
            return jsonify({'success': False, 'message': '缺少认证 Token'}), 401

        user = resolve_user_from_token(token)
        if not user:
            return jsonify({'success': False, 'message': '登录已过期，请重新登录'}), 401

        _apply_user_session(user)
        return f(*args, **kwargs)

    return decorated


def _build_auth_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'email': user.email,
        'phone': user.phone,
        'is_admin': bool(user.is_admin),
    }


def _register_default_ledger_and_account(user):
    ledger = Ledger(name=f'{user.username}的个人账本', owner_id=user.id)
    db.session.add(ledger)
    db.session.flush()

    member = LedgerMember(ledger_id=ledger.id, user_id=user.id, role='manager')
    db.session.add(member)

    account = Account(
        name='默认账户',
        balance=0,
        account_type='cash',
        user_id=user.id,
        ledger_id=ledger.id,
    )
    db.session.add(account)
    session['active_ledger_id'] = ledger.id


def _login_by_username_password():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码必填'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    user.last_login = datetime.now()
    db.session.commit()

    token = generate_token(user.id)
    _apply_user_session(user)
    return jsonify({'success': True, 'token': token, 'user': _build_auth_payload(user)})


def _register_by_username_password():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    email = (data.get('email') or '').strip() or None

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码必填'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少 6 位'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已被注册'}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '邮箱已被注册'}), 400

    user = User(username=username, email=email, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    _register_default_ledger_and_account(user)
    db.session.commit()

    token = generate_token(user.id)
    _apply_user_session(user)
    return (
        jsonify({'success': True, 'token': token, 'user': _build_auth_payload(user)}),
        201,
    )


@miniapp_bp.route('/login', methods=['POST'])
def miniapp_login():
    return _login_by_username_password()


@miniapp_bp.route('/register', methods=['POST'])
def miniapp_register():
    return _register_by_username_password()


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    return _login_by_username_password()


@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    return _register_by_username_password()


@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    token = _get_request_token()
    if token:
        _tokens.pop(token, None)
    session.clear()
    return jsonify({'success': True, 'message': '已退出登录'})


@app.route('/api/user/profile', methods=['GET'])
@login_required
def api_user_profile_get():
    user = g.user or User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'success': False, 'message': '未登录'}), 401
    return jsonify({'success': True, 'user': _build_auth_payload(user)})


@app.route('/api/user/profile', methods=['PUT'])
@login_required
def api_user_profile_update():
    user = g.user or User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json(silent=True) or {}
    nickname = data.get('nickname')
    email = data.get('email')
    phone = data.get('phone')
    avatar = data.get('avatar')

    if nickname is not None:
        user.nickname = (nickname or '').strip() or None
    if email is not None:
        normalized_email = (email or '').strip() or None
        if normalized_email and User.query.filter(User.email == normalized_email, User.id != user.id).first():
            return jsonify({'success': False, 'message': '邮箱已被其他账号使用'}), 400
        user.email = normalized_email
    if phone is not None:
        user.phone = (phone or '').strip() or None
    if avatar is not None:
        user.avatar = (avatar or '').strip() or 'default_avatar.svg'

    db.session.commit()
    return jsonify({'success': True, 'message': '资料更新成功', 'user': _build_auth_payload(user)})


@app.route('/api/user/change-password', methods=['POST'])
@login_required
def api_user_change_password():
    user = g.user or User.query.get(session.get('user_id'))
    if not user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password') or data.get('current_password') or ''
    new_password = data.get('new_password') or ''

    if not old_password or not new_password:
        return jsonify({'success': False, 'message': '旧密码和新密码不能为空'}), 400
    if not user.check_password(old_password):
        return jsonify({'success': False, 'message': '旧密码错误'}), 400
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': '新密码至少 6 位'}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({'success': True, 'message': '密码修改成功'})


@miniapp_bp.route('/dashboard', methods=['GET'])
@token_required
def miniapp_dashboard():
    user_id = session.get('user_id')
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    month = now.strftime('%Y-%m')
    current_ledger_id = get_current_ledger_id()

    tx_filters = []
    if current_ledger_id:
        tx_filters.append(Transaction.ledger_id == current_ledger_id)
    else:
        tx_filters.append(Transaction.user_id == user_id)

    month_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        *tx_filters, Transaction.type == 'income', Transaction.date.startswith(month)
    ).scalar() or 0
    month_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        *tx_filters, Transaction.type == 'expense', Transaction.date.startswith(month)
    ).scalar() or 0
    today_income = db.session.query(db.func.sum(Transaction.amount)).filter(
        *tx_filters, Transaction.type == 'income', Transaction.date == today
    ).scalar() or 0
    today_expense = db.session.query(db.func.sum(Transaction.amount)).filter(
        *tx_filters, Transaction.type == 'expense', Transaction.date == today
    ).scalar() or 0

    recent_transactions = Transaction.query.filter(*tx_filters).order_by(
        Transaction.date.desc(), Transaction.time.desc(), Transaction.id.desc()
    ).limit(5).all()

    if current_ledger_id:
        accounts = Account.query.filter_by(ledger_id=current_ledger_id).all()
    else:
        accounts = Account.query.filter_by(user_id=user_id).all()

    budget_filter = {'user_id': user_id, 'month': month}
    if current_ledger_id:
        budget_filter['ledger_id'] = current_ledger_id
    budget = Budget.query.filter_by(**budget_filter).first()

    response = {
        'success': True,
        'data': {
            'date': today,
            'current_ledger_id': current_ledger_id,
            'summary': {
                'today_income': float(today_income),
                'today_expense': float(today_expense),
                'month_income': float(month_income),
                'month_expense': float(month_expense),
                'month_balance': float(month_income) - float(month_expense),
                'balance': float(get_balance()),
            },
            'budget': {
                'id': budget.id,
                'total_amount': float(budget.total_amount),
                'remark': budget.remark or '',
            } if budget else None,
            'accounts': [
                {
                    'id': account.id,
                    'name': account.name,
                    'type': account.account_type,
                    'balance': float(account.balance or 0),
                }
                for account in accounts
            ],
            'recent_transactions': [
                {
                    'id': tx.id,
                    'type': tx.type,
                    'amount': float(tx.amount),
                    'category': tx.category,
                    'date': tx.date,
                    'time': tx.time,
                    'remark': tx.remark or '',
                    'account_name': tx.account.name if tx.account else None,
                }
                for tx in recent_transactions
            ],
        },
    }
    return jsonify(response)


@miniapp_bp.route('/upload', methods=['POST'])
@token_required
def miniapp_upload():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'success': False, 'message': '请上传文件'}), 400

    allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_ext:
        return jsonify({'success': False, 'message': '仅支持图片文件'}), 400

    upload_dir = os.path.join(app.static_folder, 'uploads', 'miniapp')
    os.makedirs(upload_dir, exist_ok=True)

    filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_{secrets.token_hex(8)}.{ext}'
    safe_name = secure_filename(filename)
    save_path = os.path.join(upload_dir, safe_name)
    file.save(save_path)

    file_url = f'/static/uploads/miniapp/{safe_name}'
    return jsonify({
        'success': True,
        'message': '上传成功',
        'file': {
            'name': safe_name,
            'url': file_url,
        },
    })
