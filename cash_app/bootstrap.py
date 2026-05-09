from datetime import date as dt_date

from .app_state import app, db
from .models import RecurringRule

# import routes for side effects
from . import routes_base, routes_transactions, routes_finance, routes_ledgers  # noqa: F401
from .routes_finance import _generate_rule_transaction
from .routes_miniapp import miniapp_bp
from .init_db import initialize_db

from blueprints.import_export import import_export_bp
from blueprints.smart_bookkeeping import smart_bp

app.register_blueprint(import_export_bp)
app.register_blueprint(smart_bp)
app.register_blueprint(miniapp_bp)


def run_startup_jobs():
    try:
        with app.app_context():
            today_str = dt_date.today().strftime('%Y-%m-%d')
            rules = RecurringRule.query.filter(
                RecurringRule.is_active == True,
                RecurringRule.next_date <= today_str,
                db.or_(RecurringRule.end_date >= today_str, RecurringRule.end_date.is_(None))
            ).all()
            gen_count = 0
            for rule in rules:
                tx = _generate_rule_transaction(rule)
                if tx:
                    gen_count += 1
            if gen_count:
                db.session.commit()
                app.logger.info(f'启动时生成周期账单 {gen_count} 笔')
    except Exception as e:
        app.logger.warning(f'启动时生成周期账单跳过: {e}')


initialize_db()
run_startup_jobs()

