import json
import secrets
from datetime import datetime, timedelta

from flask import jsonify, session, request

from .app_state import app, db
from .auth import login_required, require_ledger_access, get_user_ledger_role
from .models import Account, Budget, InviteCode, Ledger, LedgerMember, Transaction, User
from .support import get_balance

@app.route('/api/ledgers', methods=['GET'])
@login_required
def list_ledgers():
    """列出当前用户有权限的所有账本"""
    try:
        user_id = session.get('user_id')
        owned = Ledger.query.filter_by(owner_id=user_id, is_active=True).all()
        member_ledger_ids = [m.ledger_id for m in LedgerMember.query.filter_by(user_id=user_id).all()]
        member_ledgers = Ledger.query.filter(Ledger.id.in_(member_ledger_ids), Ledger.is_active == True).all() if member_ledger_ids else []
        seen = set()
        result = []
        for ledger in owned + member_ledgers:
            if ledger.id not in seen:
                seen.add(ledger.id)
                role = get_user_ledger_role(ledger.id, user_id)
                member_count = LedgerMember.query.filter_by(ledger_id=ledger.id).count()
                result.append({
                    'id': ledger.id,
                    'name': ledger.name,
                    'description': ledger.description,
                    'currency': ledger.currency,
                    'owner_id': ledger.owner_id,
                    'owner_name': ledger.owner.username if ledger.owner else None,
                    'role': role,
                    'member_count': member_count + 1,  # +1 for owner
                    'created_at': ledger.created_at.isoformat() if ledger.created_at else None,
                })
        return jsonify({'success': True, 'ledgers': result})
    except Exception as e:
        app.logger.error(f"获取账本列表失败: {e}")
        return jsonify({'success': False, 'message': '获取账本列表失败'}), 500


@app.route('/api/ledgers', methods=['POST'])
@login_required
def create_ledger():
    """创建新账本"""
    try:
        if session.get('is_admin') and not session.get('self_view'):
            return jsonify({"success": False, "message": "管理员在此模式下不能创建账本"}), 403
        data = request.get_json()
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'message': '账本名称不能为空'}), 400
        user_id = session.get('user_id')
        ledger = Ledger(name=name, description=data.get('description', ''), owner_id=user_id, currency=data.get('currency', 'CNY'))
        db.session.add(ledger)
        db.session.flush()
        member = LedgerMember(ledger_id=ledger.id, user_id=user_id, role='manager')
        db.session.add(member)
        db.session.commit()
        return jsonify({'success': True, 'message': '账本创建成功', 'ledger': {
            'id': ledger.id, 'name': ledger.name, 'description': ledger.description,
            'currency': ledger.currency, 'owner_id': ledger.owner_id, 'role': 'manager'
        }}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建账本失败: {e}")
        return jsonify({'success': False, 'message': '创建账本失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>', methods=['GET'])
@login_required
def get_ledger(ledger_id):
    """获取账本详情"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'viewer')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        member_count = LedgerMember.query.filter_by(ledger_id=ledger.id).count()
        return jsonify({'success': True, 'ledger': {
            'id': ledger.id, 'name': ledger.name, 'description': ledger.description,
            'currency': ledger.currency, 'owner_id': ledger.owner_id,
            'owner_name': ledger.owner.username if ledger.owner else None,
            'role': role, 'member_count': member_count + 1,
            'created_at': ledger.created_at.isoformat() if ledger.created_at else None,
        }})
    except Exception as e:
        app.logger.error(f"获取账本详情失败: {e}")
        return jsonify({'success': False, 'message': '获取账本详情失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>', methods=['PUT'])
@login_required
def update_ledger(ledger_id):
    """更新账本信息"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        data = request.get_json()
        if 'name' in data:
            ledger.name = data['name'].strip()
        if 'description' in data:
            ledger.description = data['description']
        if 'currency' in data:
            ledger.currency = data['currency']
        db.session.commit()
        return jsonify({'success': True, 'message': '账本更新成功'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新账本失败: {e}")
        return jsonify({'success': False, 'message': '更新账本失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>', methods=['DELETE'])
@login_required
def delete_ledger(ledger_id):
    """软删除账本"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        if ledger.owner_id != session.get('user_id'):
            return jsonify({'success': False, 'message': '只有账本所有者才能删除'}), 403
        ledger.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': '账本已删除'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"删除账本失败: {e}")
        return jsonify({'success': False, 'message': '删除账本失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/switch', methods=['POST'])
@login_required
def switch_ledger(ledger_id):
    """切换当前活动账本"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'viewer')
        if not has_access:
            return error
        session['active_ledger_id'] = ledger_id
        return jsonify({'success': True, 'message': '已切换账本', 'role': role})
    except Exception as e:
        app.logger.error(f"切换账本失败: {e}")
        return jsonify({'success': False, 'message': '切换账本失败'}), 500


# ==================== 账本成员管理 API ====================

@app.route('/api/ledgers/<int:ledger_id>/members', methods=['GET'])
@login_required
def list_members(ledger_id):
    """列出账本所有成员"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'viewer')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        owner_info = {'user_id': ledger.owner_id, 'username': ledger.owner.username if ledger.owner else '未知', 'role': 'owner'}
        members = LedgerMember.query.filter_by(ledger_id=ledger_id).all()
        member_list = [{
            'id': m.id, 'user_id': m.user_id, 'username': m.user.username if m.user else '未知',
            'role': m.role, 'joined_at': m.joined_at.isoformat() if m.joined_at else None
        } for m in members]
        return jsonify({'success': True, 'owner': owner_info, 'members': member_list})
    except Exception as e:
        app.logger.error(f"获取成员列表失败: {e}")
        return jsonify({'success': False, 'message': '获取成员列表失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/members', methods=['POST'])
@login_required
def add_member(ledger_id):
    """添加成员到账本（需 manager 权限）"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        data = request.get_json()
        username = data.get('username', '').strip()
        new_role = data.get('role', 'viewer')
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'}), 400
        if new_role not in ('viewer', 'editor', 'manager'):
            return jsonify({'success': False, 'message': '角色无效，可选: viewer, editor, manager'}), 400
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        existing = LedgerMember.query.filter_by(ledger_id=ledger_id, user_id=user.id).first()
        if existing:
            return jsonify({'success': False, 'message': '该用户已经是成员'}), 400
        member = LedgerMember(ledger_id=ledger_id, user_id=user.id, role=new_role)
        db.session.add(member)
        db.session.commit()
        return jsonify({'success': True, 'message': f'成员 {username} 添加成功'}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"添加成员失败: {e}")
        return jsonify({'success': False, 'message': '添加成员失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/members/<int:user_id>', methods=['PUT'])
@login_required
def update_member_role(ledger_id, user_id):
    """修改成员角色"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        if ledger.owner_id == user_id:
            return jsonify({'success': False, 'message': '不能修改所有者的角色'}), 400
        member = LedgerMember.query.filter_by(ledger_id=ledger_id, user_id=user_id).first_or_404()
        data = request.get_json()
        new_role = data.get('role', 'viewer')
        if new_role not in ('viewer', 'editor', 'manager'):
            return jsonify({'success': False, 'message': '角色无效'}), 400
        member.role = new_role
        db.session.commit()
        return jsonify({'success': True, 'message': '角色更新成功'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"更新成员角色失败: {e}")
        return jsonify({'success': False, 'message': '更新角色失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/members/<int:user_id>', methods=['DELETE'])
@login_required
def remove_member(ledger_id, user_id):
    """移除成员"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        ledger = Ledger.query.get_or_404(ledger_id)
        if ledger.owner_id == user_id:
            return jsonify({'success': False, 'message': '不能移除所有者'}), 400
        member = LedgerMember.query.filter_by(ledger_id=ledger_id, user_id=user_id).first_or_404()
        db.session.delete(member)
        db.session.commit()
        return jsonify({'success': True, 'message': '成员已移除'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"移除成员失败: {e}")
        return jsonify({'success': False, 'message': '移除成员失败'}), 500


# ==================== 邀请码管理 API ====================

@app.route('/api/ledgers/<int:ledger_id>/invite-codes', methods=['GET'])
@login_required
def list_invite_codes(ledger_id):
    """列出账本的邀请码"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'viewer')
        if not has_access:
            return error
        codes = InviteCode.query.filter_by(ledger_id=ledger_id).order_by(InviteCode.created_at.desc()).all()
        return jsonify({'success': True, 'invite_codes': [{
            'id': c.id, 'code': c.code, 'created_by': c.created_by,
            'creator_name': c.creator.username if c.creator else None,
            'max_uses': c.max_uses, 'used_count': c.used_count,
            'expires_at': c.expires_at.isoformat() if c.expires_at else None,
            'is_active': c.is_active, 'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in codes]})
    except Exception as e:
        app.logger.error(f"获取邀请码列表失败: {e}")
        return jsonify({'success': False, 'message': '获取邀请码列表失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/invite-codes', methods=['POST'])
@login_required
def create_invite_code(ledger_id):
    """生成邀请码（需 manager 权限）"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        data = request.get_json()
        code = secrets.token_urlsafe(16)
        max_uses = data.get('max_uses', 0)
        expires_in_hours = data.get('expires_in_hours', 0)
        expire_at = None
        if expires_in_hours > 0:
            expire_at = datetime.now() + timedelta(hours=expires_in_hours)
        invite = InviteCode(ledger_id=ledger_id, code=code, created_by=session.get('user_id'), max_uses=max_uses, expires_at=expire_at)
        db.session.add(invite)
        db.session.commit()
        return jsonify({'success': True, 'message': '邀请码创建成功', 'invite_code': {
            'id': invite.id, 'code': invite.code, 'max_uses': invite.max_uses,
            'expires_at': expire_at.isoformat() if expire_at else None
        }}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建邀请码失败: {e}")
        return jsonify({'success': False, 'message': '创建邀请码失败'}), 500


@app.route('/api/ledgers/<int:ledger_id>/invite-codes/<int:code_id>', methods=['DELETE'])
@login_required
def revoke_invite_code(ledger_id, code_id):
    """撤销邀请码"""
    try:
        has_access, role, error = require_ledger_access(ledger_id, 'manager')
        if not has_access:
            return error
        code = InviteCode.query.filter_by(id=code_id, ledger_id=ledger_id).first_or_404()
        code.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': '邀请码已撤销'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"撤销邀请码失败: {e}")
        return jsonify({'success': False, 'message': '撤销邀请码失败'}), 500


@app.route('/api/ledgers/validate-code', methods=['POST'])
@login_required
def validate_invite_code():
    """校验邀请码是否有效（不加入账本）"""
    try:
        data = request.get_json()
        code_str = data.get('code', '').strip()
        if not code_str:
            return jsonify({'valid': False, 'message': '邀请码不能为空'})
        invite = InviteCode.query.filter_by(code=code_str, is_active=True).first()
        if not invite:
            return jsonify({'valid': False, 'message': '邀请码无效或已失效'})
        if invite.expires_at and invite.expires_at < datetime.now():
            invite.is_active = False
            db.session.commit()
            return jsonify({'valid': False, 'message': '邀请码已过期'})
        if invite.max_uses > 0 and invite.used_count >= invite.max_uses:
            return jsonify({'valid': False, 'message': '邀请码已达到使用上限'})
        ledger = Ledger.query.get(invite.ledger_id)
        if not ledger or not ledger.is_active:
            return jsonify({'valid': False, 'message': '账本不存在或已停用'})
        return jsonify({'valid': True, 'message': '邀请码有效', 'ledger_name': ledger.name, 'ledger_id': ledger.id})
    except Exception as e:
        app.logger.error(f"校验邀请码失败: {e}")
        return jsonify({'valid': False, 'message': '校验失败'}), 500


@app.route('/api/ledgers/join', methods=['POST'])
@login_required
def join_ledger():
    """通过邀请码加入账本"""
    try:
        data = request.get_json()
        code_str = data.get('code', '').strip()
        if not code_str:
            return jsonify({'success': False, 'message': '邀请码不能为空'}), 400
        invite = InviteCode.query.filter_by(code=code_str, is_active=True).first()
        if not invite:
            return jsonify({'success': False, 'message': '邀请码无效或已失效'}), 404
        if invite.expires_at and invite.expires_at < datetime.now():
            invite.is_active = False
            db.session.commit()
            return jsonify({'success': False, 'message': '邀请码已过期'}), 400
        if invite.max_uses > 0 and invite.used_count >= invite.max_uses:
            return jsonify({'success': False, 'message': '邀请码已达到使用上限'}), 400
        ledger = Ledger.query.get(invite.ledger_id)
        if not ledger or not ledger.is_active:
            return jsonify({'success': False, 'message': '账本不存在或已停用'}), 404
        user_id = session.get('user_id')
        existing = LedgerMember.query.filter_by(ledger_id=invite.ledger_id, user_id=user_id).first()
        if existing:
            return jsonify({'success': False, 'message': '您已经是该账本的成员'}), 400
        member = LedgerMember(ledger_id=invite.ledger_id, user_id=user_id, role='viewer')
        db.session.add(member)
        invite.used_count += 1
        db.session.commit()
        session['active_ledger_id'] = invite.ledger_id
        return jsonify({'success': True, 'message': f'已加入账本「{ledger.name}」', 'ledger': {
            'id': ledger.id, 'name': ledger.name, 'role': 'viewer'
        }})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"加入账本失败: {e}")
        return jsonify({'success': False, 'message': '加入账本失败'}), 500


@app.route('/data.json')
@login_required
def get_json_data():
    try:
        # 根据权限过滤数据
        user_id = session.get('user_id')
        is_admin = session.get('is_admin')
        self_view = session.get('self_view', False)
        current_ledger_id = get_current_ledger_id()

        if current_ledger_id:
            transactions = Transaction.query.filter(Transaction.ledger_id == current_ledger_id).order_by(Transaction.id.desc()).all()
        elif user_id and is_admin and not self_view:
            transactions = Transaction.query.order_by(Transaction.id.desc()).all()
        elif user_id:
            transactions = Transaction.query.filter(Transaction.user_id == user_id).order_by(Transaction.id.desc()).all()
        else:
            transactions = Transaction.query.order_by(Transaction.id.desc()).all()
        categories = [c.name for c in Category.query.all()]
        return jsonify({
            "transactions": [
                {
                    "id": t.id,
                    "type": t.type,
                    "amount": t.amount,
                    "category": t.category,
                    "date": t.date,
                    "time": t.time,
                    "remark": t.remark,
                    "currency": t.currency or 'CNY',
                    "original_amount": float(t.original_amount) if t.original_amount else None,
                    "exchange_rate": float(t.exchange_rate) if t.exchange_rate else None,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                    "reimbursement_status": t.reimbursement_status or 'none',
                    "reimbursed_amount": float(t.reimbursed_amount) if t.reimbursed_amount else 0,
                    "write_off_id": t.write_off_id,
                    "user_id": t.user_id,
                    "username": t.user.username if t.user else None,
                    "payer_user_id": t.payer_user_id,
                    "split_details": json.loads(t.split_details) if t.split_details else []
                } for t in transactions
            ],
            "categories": categories,
            "balance": get_balance()
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": 500}), 500



