from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for

from .app_state import app
from .models import Ledger, LedgerMember, User


def _get_user_from_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header:
        return None
    try:
        from .routes_miniapp import resolve_user_from_token
    except Exception:
        return None

    user = resolve_user_from_token(auth_header)
    if not user:
        return None

    g.user = user
    session['user_id'] = user.id
    session['is_admin'] = bool(user.is_admin)
    session.setdefault('self_view', True)
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            _get_user_from_token()
        if not session.get('user_id'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': '登录已过期，请刷新页面'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_admin(*args, **kwargs):
        if not session.get('user_id'):
            _get_user_from_token()
        if not session.get('user_id') or not session.get('is_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': '登录已过期，请刷新页面'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_admin


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = _get_user_from_token()
    else:
        g.user = User.query.get(user_id)


def get_user_ledger_role(ledger_id, user_id):
    """获取用户在账本中的角色，返回 None 表示非成员"""
    member = LedgerMember.query.filter_by(ledger_id=ledger_id, user_id=user_id).first()
    if member:
        return member.role
    ledger = Ledger.query.get(ledger_id)
    if ledger and ledger.owner_id == user_id:
        return 'manager'
    return None


def require_ledger_access(ledger_id, min_role='viewer'):
    """检查当前用户是否有至少 min_role 的权限
    返回 (has_access, role, error_response)"""
    user_id = session.get('user_id')
    if not user_id:
        _get_user_from_token()
        user_id = session.get('user_id')
    if not user_id:
        return False, None, (jsonify({'success': False, 'message': '未登录'}), 401)

    # 管理员在后台模式(self_view=False)下拥有全部访问权限
    # 但在前台查看共享账本时需遵守账本权限
    if session.get('is_admin') and not session.get('self_view', True):
        return True, 'manager', None

    role = get_user_ledger_role(ledger_id, user_id)
    if not role:
        return False, None, (jsonify({'success': False, 'message': '无权限访问该账本'}), 403)
    role_hierarchy = {'viewer': 0, 'editor': 1, 'manager': 2}
    if role_hierarchy.get(role, -1) < role_hierarchy.get(min_role, 0):
        return False, role, (jsonify({'success': False, 'message': '权限不足'}), 403)
    return True, role, None


def get_current_ledger_id():
    """获取当前活动账本 ID，从 session 读取，回退到用户第一个账本"""
    ledger_id = session.get('active_ledger_id')
    user_id = session.get('user_id')
    if not user_id:
        _get_user_from_token()
        user_id = session.get('user_id')
    if not user_id:
        return None

    if ledger_id:
        member = LedgerMember.query.filter_by(ledger_id=ledger_id, user_id=user_id).first()
        if member:
            return ledger_id
        owned = Ledger.query.filter_by(id=ledger_id, owner_id=user_id).first()
        if owned:
            return ledger_id

    membership = LedgerMember.query.filter_by(user_id=user_id).first()
    if membership:
        session['active_ledger_id'] = membership.ledger_id
        return membership.ledger_id

    owned = Ledger.query.filter_by(owner_id=user_id).first()
    if owned:
        session['active_ledger_id'] = owned.id
        return owned.id
    return None


# 首页、admin页路由权限修改（index和admin_dashboard分别加装饰器）
