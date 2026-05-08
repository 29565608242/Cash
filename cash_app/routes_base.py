import os
import uuid
from datetime import datetime
from functools import wraps

from flask import g, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import generate_password_hash

from .app_state import app
from .auth import admin_required, login_required
from .models import Account, Ledger, LedgerMember, Transaction, User, db

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        is_admin = role == 'admin'
        user = User.query.filter_by(username=username, is_admin=is_admin).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            if is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        error = '管理员账号或密码错误' if is_admin else '用户名或密码错误'
        return render_template('login.html', error=error)
    reset_success = request.args.get('reset_success')
    return render_template('login.html', reset_success=reset_success)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """保留旧路由兼容，重定向到统一登录页"""
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if not username or not password:
            return render_template('register.html', error='用户名和密码必填')
        if password != password2:
            return render_template('register.html', error='两次输入的密码不一致')
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='用户名已被注册')
        email = request.form.get('email')
        if email and User.query.filter_by(email=email).first():
            return render_template('register.html', error='邮箱已被注册')
        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # 为新用户创建默认个人账本和默认账户
        ledger = Ledger(name=f"{username}的个人账本", owner_id=user.id)
        db.session.add(ledger)
        db.session.flush()
        member = LedgerMember(ledger_id=ledger.id, user_id=user.id, role='manager')
        db.session.add(member)
        account = Account(name='默认账户', balance=0, account_type='cash', user_id=user.id, ledger_id=ledger.id)
        db.session.add(account)

        db.session.commit()
        # 注册成功后提示并2秒后自动跳转
        return render_template('register.html', success='注册成功，2秒后自动跳转登录页面~', redirect_login=True)
    return render_template('register.html')

# 登录校验装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 忘记密码路由
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        if not username or not email:
            return render_template('forgot_password.html', error='用户名和邮箱必须填写')

        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template('forgot_password.html', error='用户不存在')

        if not user.email or user.email != email:
            return render_template('forgot_password.html', error='邮箱不匹配，请使用注册时填写的邮箱')

        session['reset_allowed'] = True
        session['reset_username'] = username

        return render_template('reset_password.html', username=username)

    return render_template('forgot_password.html')


# 密码重置路由
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 验证是否通过 forgot-password 页面允许
        if not session.get('reset_allowed') or session.get('reset_username') != username:
            return redirect(url_for('forgot_password'))

        if not username or not new_password or not confirm_password:
            return render_template('reset_password.html', error='所有字段都必须填写')

        if new_password != confirm_password:
            return render_template('reset_password.html', error='新密码和确认密码不一致')

        if len(new_password) < 6:
            return render_template('reset_password.html', error='密码长度不能少于6位')

        user = User.query.filter_by(username=username).first()
        if not user:
            return render_template('reset_password.html', error='用户不存在')

        # 更新密码
        user.set_password(new_password)
        db.session.commit()

        # 清除重置标识
        session.pop('reset_allowed', None)
        session.pop('reset_username', None)

        # 跳转到登录页并提示成功
        return redirect(url_for('login', reset_success=1))

    username = request.args.get('username', '')
    # 没有 session 标识则不让直接访问重置页
    if not session.get('reset_allowed') or session.get('reset_username') != username:
        return redirect(url_for('forgot_password'))
    return render_template('reset_password.html', username=username)

# 用户信息路由
@app.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 处理头像上传（立即提交，确保头像独立保存）
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            import os
            import uuid
            from werkzeug.utils import secure_filename

            # 验证文件类型
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
            ext = avatar_file.filename.rsplit('.', 1)[-1].lower() if '.' in avatar_file.filename else ''
            if ext not in allowed_extensions:
                return render_template('user_profile.html', error='仅支持 JPG、PNG、GIF、SVG、WebP 格式的图片', user=user)

            # 确保avatars目录存在
            avatar_dir = os.path.join(app.static_folder, 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)

            # 生成唯一文件名，防止冲突
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(avatar_dir, unique_name)

            # 删除旧头像（如果不是默认头像）
            if user.avatar and user.avatar not in ('default_avatar.svg', 'default_avatar.png'):
                old_path = os.path.join(avatar_dir, user.avatar)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 保存文件
            avatar_file.save(file_path)
            user.avatar = unique_name
            db.session.commit()  # 立即提交头像变更

        # 更新用户信息
        new_email = request.form.get('email')
        new_phone = request.form.get('phone')
        new_nickname = request.form.get('nickname')

        user.email = new_email
        user.phone = new_phone
        user.nickname = new_nickname

        db.session.commit()

        # 重新查询用户以获取最新数据
        user = User.query.get(session['user_id'])

        return render_template('user_profile.html', success='个人信息更新成功', user=user)

    return render_template('user_profile.html', user=user)

# 密码修改路由（在用户信息模块中）
@app.route('/user-profile/change-password', methods=['GET', 'POST'])
@login_required
def user_profile_change_password():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 验证输入
        if not current_password or not new_password or not confirm_password:
            return render_template('user_profile.html', error='所有字段都必须填写', user=user)

        if new_password != confirm_password:
            return render_template('user_profile.html', error='新密码和确认密码不一致', user=user)

        # 验证当前密码
        if not user.check_password(current_password):
            return render_template('user_profile.html', error='当前密码错误', user=user)

        # 更新密码
        user.set_password(new_password)
        db.session.commit()

        # 清除会话并要求重新登录
        session.clear()
        return render_template('user_profile.html', success='密码修改成功，请重新登录', user=user)

    return render_template('user_profile.html', user=user)


@app.route('/')
@login_required
def index():
    """首页 - 普通用户使用；管理员统一留在后台"""
    username = g.user.username if g.user else None
    is_admin = g.user.is_admin if g.user else False
    if is_admin:
        session['self_view'] = False
        return redirect(url_for('admin_dashboard'))

    session['self_view'] = True
    from .auth import get_current_ledger_id
    from .models import Ledger
    active_ledger_id = get_current_ledger_id()
    ledgers = Ledger.query.filter_by(owner_id=g.user.id, is_active=True).all() if g.user else []
    return render_template('index.html', username=username, is_admin=is_admin, self_view=False, active_ledger_id=active_ledger_id, ledgers=ledgers)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """后台管理页面 - 管理员查看所有用户的数据"""
    session['self_view'] = False
    session.pop('active_ledger_id', None)
    try:
        # 所有用户（排除管理员，仅用于前台展示和筛选）
        users = User.query.all()
        user_list = [{
            'id': u.id,
            'username': u.username,
            'is_admin': u.is_admin,
            'email': u.email,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else '',
            'last_login': u.last_login.strftime('%Y-%m-%d %H:%M:%S') if u.last_login else ''
        } for u in users if not u.is_admin]

        # 所有交易统计
        total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='income').scalar() or 0
        total_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='expense').scalar() or 0
        total_balance = float(total_income - total_expense)

        # 今日数据
        today = datetime.now().strftime('%Y-%m-%d')
        today_transactions = Transaction.query.filter(Transaction.date == today).all()
        today_income = sum(float(t.amount) for t in today_transactions if t.type == 'income')
        today_expense = sum(float(t.amount) for t in today_transactions if t.type == 'expense')

        # 每个用户的统计数据（排除管理员）
        user_stats = []
        for u in users:
            if u.is_admin:
                continue
            u_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='income', user_id=u.id).scalar() or 0
            u_expense = db.session.query(db.func.sum(Transaction.amount)).filter_by(type='expense', user_id=u.id).scalar() or 0
            u_count = Transaction.query.filter_by(user_id=u.id).count()
            user_stats.append({
                'username': u.username,
                'income': float(u_income),
                'expense': float(u_expense),
                'balance': float(u_income - u_expense),
                'count': u_count
            })

        return render_template('admin.html',
            balance=total_balance,
            today_income=float(today_income),
            today_expense=float(today_expense),
            total_income=float(total_income),
            total_expense=float(total_expense),
            user_stats=user_stats,
            users=user_list
        )
    except Exception as e:
        # 记录错误并返回错误页面
        app.logger.error(f"Admin dashboard error: {str(e)}")
        return render_template('error.html', error="系统错误，请稍后再试")

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('create_admin.html', error='用户名和密码不能为空')

        if User.query.filter_by(username=username).first():
            return render_template('create_admin.html', error='用户名已存在')

        admin = User(username=username, password_hash=generate_password_hash(password), is_admin=True)
        db.session.add(admin)
        db.session.commit()

        return render_template('create_admin.html', success='管理员创建成功！')

    return render_template('create_admin.html')


# 报表页面
@app.route('/reports')
@login_required
def reports_page():
    """财务报表页面"""
    return render_template('reports.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """静态文件路由"""
    return send_from_directory(app.static_folder, filename)


# ==================== API 路由 ====================

