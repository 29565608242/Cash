from .app_state import app, db
from .models import (AIAnalysis, Account, Budget, Category, InviteCode, Ledger,
                     LedgerMember, MoneyChangeLog, Transaction, User)

# 淇濊瘉琛ㄥ凡瀛樺湪
def initialize_db():
    with app.app_context():
        db.create_all()

        # ---- 鏁版嵁搴撹縼绉伙細涓?users 琛ㄦ坊鍔犲悗缁柊澧炵殑瀛楁锛堝繀椤诲湪浠讳綍 ORM 鏌ヨ鍓嶆墽琛岋級 ----
        for col_def in [
            ('avatar', 'ALTER TABLE users ADD COLUMN avatar VARCHAR(255) DEFAULT "default_avatar.svg"'),
            ('email', 'ALTER TABLE users ADD COLUMN email VARCHAR(120) DEFAULT NULL'),
            ('phone', 'ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL'),
            ('nickname', 'ALTER TABLE users ADD COLUMN nickname VARCHAR(64) DEFAULT NULL'),
            ('created_at', 'ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('last_login', 'ALTER TABLE users ADD COLUMN last_login DATETIME DEFAULT NULL'),
        ]:
            col_name, alter_sql = col_def
            try:
                db.session.execute(db.text(f'SELECT {col_name} FROM users LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(alter_sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁杩佺Щ锛氭洿鏂拌佺敤鎴风殑榛樿澶村儚锛坧ng -> svg锛----
        try:
            db.session.execute(db.text(
                "UPDATE users SET avatar = 'default_avatar.svg' WHERE avatar = 'default_avatar.png'"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?Category 琛ㄦ坊鍔?type 瀛楁 ----
        try:
            db.session.execute(db.text('SELECT type FROM categories LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE categories ADD COLUMN type VARCHAR(10) NOT NULL DEFAULT "expense"'))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?transactions 琛ㄦ坊鍔?account_id / user_id 瀛楁 ----
        for col_def in [
            ('account_id', 'ALTER TABLE transactions ADD COLUMN account_id INT DEFAULT NULL'),
            ('user_id', 'ALTER TABLE transactions ADD COLUMN user_id INT DEFAULT NULL'),
        ]:
            col_name, alter_sql = col_def
            try:
                db.session.execute(db.text(f'SELECT {col_name} FROM transactions LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(alter_sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?transactions 琛ㄦ坊鍔?currency / original_amount / exchange_rate 瀛楁 ----
        for col_def in [
            ('currency', 'ALTER TABLE transactions ADD COLUMN currency VARCHAR(10) DEFAULT "CNY"'),
            ('original_amount', 'ALTER TABLE transactions ADD COLUMN original_amount DECIMAL(10,2) DEFAULT NULL'),
            ('exchange_rate', 'ALTER TABLE transactions ADD COLUMN exchange_rate DECIMAL(10,6) DEFAULT NULL'),
        ]:
            col_name, alter_sql = col_def
            try:
                db.session.execute(db.text(f'SELECT {col_name} FROM transactions LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(alter_sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?transactions 琛ㄦ坊鍔?reimbursement 鐩稿叧瀛楁 ----
        for col_def in [
            ('reimbursement_status', 'ALTER TABLE transactions ADD COLUMN reimbursement_status VARCHAR(20) DEFAULT "none"'),
            ('reimbursed_amount', 'ALTER TABLE transactions ADD COLUMN reimbursed_amount DECIMAL(10,2) DEFAULT 0'),
            ('write_off_id', 'ALTER TABLE transactions ADD COLUMN write_off_id INT DEFAULT NULL'),
        ]:
            col_name, alter_sql = col_def
            try:
                db.session.execute(db.text(f'SELECT {col_name} FROM transactions LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(alter_sql))
                    db.session.commit()
                    # Add FK constraint for write_off_id
                    if col_name == 'write_off_id':
                        try:
                            db.session.execute(db.text(
                                'ALTER TABLE transactions ADD CONSTRAINT fk_write_off FOREIGN KEY (write_off_id) REFERENCES transactions(id) ON DELETE SET NULL'
                            ))
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?budgets / budget_category_items 寤鸿〃 ----
        try:
            db.session.execute(db.text('SELECT 1 FROM budgets LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS budgets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        account_id INT DEFAULT NULL,
                        month VARCHAR(7) NOT NULL,
                        total_amount DECIMAL(10,2) NOT NULL,
                        remark VARCHAR(255),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    )
                '''))
                db.session.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS budget_category_items (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        budget_id INT NOT NULL,
                        category_id INT NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        FOREIGN KEY (budget_id) REFERENCES budgets(id),
                        FOREIGN KEY (category_id) REFERENCES categories(id)
                    )
                '''))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?budgets 琛ㄦ坊鍔?account_id 瀛楁 ----
        try:
            db.session.execute(db.text('SELECT account_id FROM budgets LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE budgets ADD COLUMN account_id INT DEFAULT NULL, ADD FOREIGN KEY (account_id) REFERENCES accounts(id)'))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細export_tasks / file_uploads 琛?----
        for table_name, create_sql in [
            ('export_tasks', '''
                CREATE TABLE IF NOT EXISTS export_tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    progress INT DEFAULT 0,
                    file_format VARCHAR(10) NOT NULL,
                    file_path VARCHAR(500),
                    file_size INT,
                    filters TEXT,
                    total_records INT DEFAULT 0,
                    error_message TEXT,
                    email_to VARCHAR(200),
                    email_sent TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            '''),
            ('file_uploads', '''
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    upload_id VARCHAR(36) UNIQUE NOT NULL,
                    user_id INT NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_format VARCHAR(10) NOT NULL,
                    total_rows INT DEFAULT 0,
                    columns TEXT,
                    preview_data TEXT,
                    status VARCHAR(20) DEFAULT 'uploaded',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            '''),
        ]:
            try:
                db.session.execute(db.text(f'SELECT 1 FROM {table_name} LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(create_sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 榛樿鍒嗙被 ----
        if Category.query.count() == 0:
            default_income = ['工资', '奖金', '投资收益', '兼职', '红包', '报销收入', '其他收入']
            default_expense = ['餐饮', '交通', '购物', '娱乐', '医疗', '住房', '教育', '通讯', '其他支出']
            for cname in default_income:
                db.session.add(Category(name=cname, type='income'))
            for cname in default_expense:
                db.session.add(Category(name=cname, type='expense'))
        # ---- 清理乱码分类 ----
        try:
            garbled = Category.query.filter(Category.name.like('%鎶%'), Category.type == 'income').all()
            for g in garbled:
                db.session.delete(g)
            db.session.commit()
        except Exception:
            db.session.rollback()

        if Category.query.count() > 0 and not Category.query.filter_by(name='报销收入', type='income').first():
            db.session.add(Category(name='报销收入', type='income'))

        # ---- 榛樿鐢ㄦ埛 ----
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        if not User.query.filter_by(username='user').first():
            user = User(username='user', is_admin=False)
            user.set_password('user123')
            db.session.add(user)
        db.session.commit()

        # ---- 鏁版嵁搴撹縼绉伙細鍒涘缓璐︽湰鐩稿叧琛?----
        for table_name, create_sql in [
            ('ledgers', '''
                CREATE TABLE IF NOT EXISTS ledgers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description VARCHAR(255),
                    owner_id INT NOT NULL,
                    currency VARCHAR(10) DEFAULT 'CNY',
                    is_active TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id)
                )
            '''),
            ('ledger_members', '''
                CREATE TABLE IF NOT EXISTS ledger_members (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ledger_id INT NOT NULL,
                    user_id INT NOT NULL,
                    role VARCHAR(20) DEFAULT 'viewer',
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ledger_id) REFERENCES ledgers(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE KEY uq_ledger_user (ledger_id, user_id)
                )
            '''),
            ('invite_codes', '''
                CREATE TABLE IF NOT EXISTS invite_codes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ledger_id INT NOT NULL,
                    code VARCHAR(64) UNIQUE NOT NULL,
                    created_by INT NOT NULL,
                    max_uses INT DEFAULT 0,
                    used_count INT DEFAULT 0,
                    expires_at DATETIME,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ledger_id) REFERENCES ledgers(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            '''),
        ]:
            try:
                db.session.execute(db.text(f'SELECT 1 FROM {table_name} LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(create_sql))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?accounts / transactions / budgets 娣诲姞 ledger_id 瀛楁 ----
        # 鍏堜负 accounts 娣诲姞锛屽悗缁垱寤洪粯璁よ处鎴锋椂 ORM 涓嶄細鎶ラ敊
        for table_name in ['accounts', 'transactions', 'budgets']:
            try:
                db.session.execute(db.text(f'SELECT ledger_id FROM {table_name} LIMIT 0'))
            except Exception:
                try:
                    db.session.execute(db.text(f'ALTER TABLE {table_name} ADD COLUMN ledger_id INT DEFAULT NULL'))
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?transactions 娣诲姞 payer_user_id 瀛楁 ----
        try:
            db.session.execute(db.text('SELECT payer_user_id FROM transactions LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE transactions ADD COLUMN payer_user_id INT DEFAULT NULL'))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細涓?transactions 娣诲姞 split_details 瀛楁 ----
        try:
            db.session.execute(db.text('SELECT split_details FROM transactions LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE transactions ADD COLUMN split_details TEXT DEFAULT NULL'))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 涓烘病鏈夎处鎴风殑鐢ㄦ埛鍒涘缓榛樿璐︽埛锛堝甫 ledger_id锛?----
        for u in User.query.all():
            if Account.query.filter_by(user_id=u.id).count() == 0:
                db.session.add(Account(name='榛樿璐︽埛', balance=0, account_type='cash', user_id=u.id))
        db.session.commit()

        # ---- 涓哄凡鏈夌敤鎴峰垱寤轰釜浜洪粯璁よ处鏈?----
        for u in User.query.all():
            if Ledger.query.filter_by(owner_id=u.id).count() == 0:
                ledger = Ledger(name=f"{u.username}的个人账本", owner_id=u.id)
                db.session.add(ledger)
                db.session.flush()
                member = LedgerMember(ledger_id=ledger.id, user_id=u.id, role='manager')
                db.session.add(member)
                Transaction.query.filter_by(user_id=u.id, ledger_id=None).update({'ledger_id': ledger.id})
                Account.query.filter_by(user_id=u.id, ledger_id=None).update({'ledger_id': ledger.id})
                Budget.query.filter_by(user_id=u.id, ledger_id=None).update({'ledger_id': ledger.id})
        db.session.commit()

        # ---- 鏁版嵁搴撹縼绉伙細鍒涘缓鍊熻捶琛?----
        try:
            db.session.execute(db.text('SELECT 1 FROM loans LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS loans (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        ledger_id INT DEFAULT NULL,
                        type VARCHAR(10) NOT NULL,
                        counterparty VARCHAR(100) NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        repaid_amount DECIMAL(10,2) DEFAULT 0,
                        date VARCHAR(20) NOT NULL,
                        due_date VARCHAR(20) DEFAULT NULL,
                        status VARCHAR(20) DEFAULT 'active',
                        remark VARCHAR(255) DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
                    )
                '''))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 鏁版嵁搴撹縼绉伙細鍒涘缓 AI 鍒嗘瀽琛?----
        try:
            db.session.execute(db.text('SELECT 1 FROM ai_analysis LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS ai_analysis (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        period VARCHAR(20) NOT NULL,
                        start_date VARCHAR(20) NOT NULL,
                        end_date VARCHAR(20) NOT NULL,
                        analysis_content TEXT NOT NULL,
                        model_used VARCHAR(50) NOT NULL,
                        prompt_tokens INT DEFAULT 0,
                        completion_tokens INT DEFAULT 0,
                        total_tokens INT DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        is_deleted TINYINT(1) DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                '''))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # ---- 数据迁移：创建资金变动记录表 ----
        try:
            db.session.execute(db.text('SELECT 1 FROM money_change_logs LIMIT 0'))
        except Exception:
            try:
                db.session.execute(db.text('''
                    CREATE TABLE IF NOT EXISTS money_change_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        ledger_id INT DEFAULT NULL,
                        account_id INT DEFAULT NULL,
                        action_type VARCHAR(20) NOT NULL,
                        entity_type VARCHAR(20) NOT NULL,
                        entity_id INT DEFAULT NULL,
                        amount_change DECIMAL(10,2) DEFAULT 0,
                        balance_before DECIMAL(10,2) DEFAULT NULL,
                        balance_after DECIMAL(10,2) DEFAULT NULL,
                        description VARCHAR(500) DEFAULT NULL,
                        details TEXT DEFAULT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (ledger_id) REFERENCES ledgers(id),
                        FOREIGN KEY (account_id) REFERENCES accounts(id)
                    )
                '''))
                db.session.commit()
            except Exception:
                db.session.rollback()

