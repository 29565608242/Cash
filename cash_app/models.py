from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .app_state import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    remark = db.Column(db.String(255))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    currency = db.Column(db.String(10), default='CNY')
    original_amount = db.Column(db.Numeric(10, 2), nullable=True)
    exchange_rate = db.Column(db.Numeric(10, 6), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    reimbursement_status = db.Column(db.String(20), default='none')  # none, pending, partial, reimbursed
    reimbursed_amount = db.Column(db.Numeric(10, 2), default=0)
    write_off_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)

    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    payer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    split_details = db.Column(db.Text, nullable=True)

    account = db.relationship('Account', backref=db.backref('transactions', lazy='dynamic'))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('transactions', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('transactions', lazy='dynamic'))
    payer_user = db.relationship('User', foreign_keys=[payer_user_id], backref=db.backref('paid_transactions', lazy='dynamic'))

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False, default='expense')

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0)
    account_type = db.Column(db.String(20), default='cash')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('accounts', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('accounts', lazy='dynamic'))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(255), nullable=True, default='default_avatar.svg')
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    nickname = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Budget(db.Model):
    __tablename__ = 'budgets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    month = db.Column(db.String(7), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('budgets', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('budgets', lazy='dynamic'))
    account = db.relationship('Account', backref=db.backref('budgets', lazy='dynamic'))


class BudgetCategoryItem(db.Model):
    __tablename__ = 'budget_category_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    budget = db.relationship('Budget', backref=db.backref('category_items', lazy='dynamic'))
    category = db.relationship('Category')


class ExportTask(db.Model):
    __tablename__ = 'export_tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)
    file_format = db.Column(db.String(10), nullable=False)  # csv, xlsx
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    filters = db.Column(db.Text)  # JSON string
    total_records = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    email_to = db.Column(db.String(200))
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('export_tasks', lazy='dynamic'))


class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    upload_id = db.Column(db.String(36), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_format = db.Column(db.String(10), nullable=False)
    total_rows = db.Column(db.Integer, default=0)
    columns = db.Column(db.Text)  # JSON
    preview_data = db.Column(db.Text)  # JSON
    status = db.Column(db.String(20), default='uploaded')  # uploaded, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('file_uploads', lazy='dynamic'))


class Ledger(db.Model):
    __tablename__ = 'ledgers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(db.String(10), default='CNY')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    owner = db.relationship('User', backref=db.backref('owned_ledgers', lazy='dynamic'))


class LedgerMember(db.Model):
    __tablename__ = 'ledger_members'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # viewer, editor, manager
    joined_at = db.Column(db.DateTime, default=datetime.now)

    ledger = db.relationship('Ledger', backref=db.backref('members', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('ledger_memberships', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('ledger_id', 'user_id', name='uq_ledger_user'),)


class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    period = db.Column(db.String(20), nullable=False)  # month, week, year
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    analysis_content = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(50), nullable=False)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('ai_analyses', lazy='dynamic'))


class InviteCode(db.Model):
    __tablename__ = 'invite_codes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    max_uses = db.Column(db.Integer, default=0)  # 0 = unlimited
    used_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    ledger = db.relationship('Ledger', backref=db.backref('invite_codes', lazy='dynamic'))
    creator = db.relationship('User', backref=db.backref('created_invite_codes', lazy='dynamic'))


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    type = db.Column(db.String(10), nullable=False)  # 'borrow' 鍊熷叆(璐熷€?, 'lend' 鍊熷嚭(鍊烘潈)
    counterparty = db.Column(db.String(100), nullable=False)  # 瀵规柟鍚嶇О
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 总金额
    repaid_amount = db.Column(db.Numeric(10, 2), default=0)  # 已还/已收金额
    date = db.Column(db.String(20), nullable=False)  # 鍊熻捶鏃ユ湡
    due_date = db.Column(db.String(20), nullable=True)  # 到期日
    status = db.Column(db.String(20), default='active')  # 'active', 'settled'
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('loans', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('loans', lazy='dynamic'))


class RecurringRule(db.Model):
    """鍛ㄦ湡璐﹀崟瑙勫垯"""
    __tablename__ = 'recurring_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)  # 璐﹀崟鍚嶇О
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 閲戦
    category = db.Column(db.String(50), nullable=False)  # 鍒嗙被
    type = db.Column(db.String(10), nullable=False)  # income / expense
    period = db.Column(db.String(20), nullable=False)  # daily / weekly / monthly / yearly
    interval_value = db.Column(db.Integer, default=1)  # 闂撮殧鍊硷紝濡傛瘡2鍛ㄣ€佹瘡3涓湀
    start_date = db.Column(db.String(20), nullable=False)  # 寮€濮嬫棩鏈?YYYY-MM-DD
    end_date = db.Column(db.String(20), nullable=True)  # 缁撴潫鏃ユ湡 YYYY-MM-DD
    next_date = db.Column(db.String(20), nullable=False)  # 涓嬫鐢熸垚鏃ユ湡 YYYY-MM-DD
    is_active = db.Column(db.Boolean, default=True)
    remark = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    user = db.relationship('User', backref=db.backref('recurring_rules', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('recurring_rules', lazy='dynamic'))
    account = db.relationship('Account', backref=db.backref('recurring_rules', lazy='dynamic'))


class MoneyChangeLog(db.Model):
    """资金变动记录"""
    __tablename__ = 'money_change_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ledger_id = db.Column(db.Integer, db.ForeignKey('ledgers.id'), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    action_type = db.Column(db.String(20), nullable=False)  # create/update/delete/adjust/repay/import
    entity_type = db.Column(db.String(20), nullable=False)  # transaction/account/loan
    entity_id = db.Column(db.Integer, nullable=True)
    amount_change = db.Column(db.Numeric(10, 2), default=0)
    balance_before = db.Column(db.Numeric(10, 2), nullable=True)
    balance_after = db.Column(db.Numeric(10, 2), nullable=True)
    description = db.Column(db.String(500))
    details = db.Column(db.Text, nullable=True)  # JSON extra context
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('money_change_logs', lazy='dynamic'))
    ledger = db.relationship('Ledger', backref=db.backref('money_change_logs', lazy='dynamic'))
    account = db.relationship('Account', backref=db.backref('money_change_logs', lazy='dynamic'))

