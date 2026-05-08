"""
智能记账模块 - 解析自然语言/语音识别/图片识别结果为账单，提供智能校验和去重检测
"""
from flask import Blueprint, request, jsonify, session, g, current_app
from datetime import datetime, timedelta
import calendar
import re
import json
import logging
import requests
from sqlalchemy import func

smart_bp = Blueprint('smart_bookkeeping', __name__, url_prefix='/api/smart')
logger = logging.getLogger(__name__)

# ==================== 导入 app 中的模型 ====================
def _import_models():
    """延迟导入避免循环依赖"""
    from app import db, Transaction, Category, Account, AIAnalysis
    return db, Transaction, Category, Account, AIAnalysis


def _get_log_helper():
    """延迟导入避免循环依赖"""
    from cash_app.support import log_money_change as _lmc
    return _lmc


def _build_period_range(period, start_date=None, end_date=None):
    """Build the date range used by reports and AI analysis."""
    now = datetime.now()

    if period == 'week':
        start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        end = now.strftime('%Y-%m-%d')
    elif period == 'month':
        start = now.strftime('%Y-%m-01')
        end = now.strftime('%Y-%m-%d')
    elif period == 'quarter':
        current_quarter = (now.month - 1) // 3 + 1
        start_month = (current_quarter - 1) * 3 + 1
        start = f'{now.year}-{start_month:02d}-01'
        last_day = calendar.monthrange(now.year, start_month + 2)[1]
        end = f'{now.year}-{start_month + 2:02d}-{last_day}'
    elif period == 'year':
        start = f'{now.year}-01-01'
        end = now.strftime('%Y-%m-%d')
    elif period == 'custom':
        start = start_date or (now - timedelta(days=30)).strftime('%Y-%m-%d')
        end = end_date or now.strftime('%Y-%m-%d')
    else:
        start = now.strftime('%Y-%m-01')
        end = now.strftime('%Y-%m-%d')

    return start, end


def _build_analysis_dataset(user_id, period, start_date=None, end_date=None):
    """Collect report-like transaction data for AI analysis."""
    _, Transaction, _, _, _ = _import_models()
    from app import get_current_ledger_id

    start, end = _build_period_range(period, start_date, end_date)
    query = Transaction.query.filter(
        Transaction.date >= start,
        Transaction.date <= end
    )

    current_ledger_id = get_current_ledger_id()
    is_admin = session.get('is_admin')
    self_view = session.get('self_view', False)

    if current_ledger_id:
        query = query.filter(Transaction.ledger_id == current_ledger_id)
    elif user_id and (not is_admin or self_view):
        query = query.filter(Transaction.user_id == user_id)

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    if not transactions:
        return None

    income = float(sum(float(t.amount or 0) for t in transactions if t.type == 'income'))
    expense = float(sum(float(t.amount or 0) for t in transactions if t.type == 'expense'))
    date_diff = max(1, (datetime.strptime(end, '%Y-%m-%d') - datetime.strptime(start, '%Y-%m-%d')).days + 1)

    category_stats = {}
    daily_trend = {}
    for t in transactions:
        key = f"{t.type}:{t.category}"
        if key not in category_stats:
            category_stats[key] = {'type': t.type, 'category': t.category, 'amount': 0.0, 'count': 0}
        category_stats[key]['amount'] += float(t.amount or 0)
        category_stats[key]['count'] += 1

        if t.date not in daily_trend:
            daily_trend[t.date] = {'income': 0.0, 'expense': 0.0, 'count': 0}
        if t.type == 'income':
            daily_trend[t.date]['income'] += float(t.amount or 0)
        else:
            daily_trend[t.date]['expense'] += float(t.amount or 0)
        daily_trend[t.date]['count'] += 1

    expense_category_stats = sorted(
        [v for v in category_stats.values() if v['type'] == 'expense'],
        key=lambda item: item['amount'],
        reverse=True
    )
    income_category_stats = sorted(
        [v for v in category_stats.values() if v['type'] == 'income'],
        key=lambda item: item['amount'],
        reverse=True
    )

    return {
        'period': period,
        'start_date': start,
        'end_date': end,
        'summary': {
            'income': round(income, 2),
            'expense': round(expense, 2),
            'net': round(income - expense, 2),
            'count': len(transactions),
            'days': date_diff,
            'avg_daily_income': round(income / date_diff, 2) if income else 0,
            'avg_daily_expense': round(expense / date_diff, 2) if expense else 0,
        },
        'top_expense_categories': expense_category_stats[:5],
        'top_income_categories': income_category_stats[:5],
        'daily_trend': [
            {
                'date': date_key,
                'income': round(stats['income'], 2),
                'expense': round(stats['expense'], 2),
                'count': stats['count'],
            }
            for date_key, stats in sorted(daily_trend.items())
        ],
        'recent_transactions': [
            {
                'type': t.type,
                'amount': float(t.amount or 0),
                'category': t.category,
                'date': t.date,
                'time': t.time,
                'remark': t.remark or '',
            }
            for t in transactions[:20]
        ],
    }


def _call_deepseek_analysis(dataset):
    """Call DeepSeek to generate bookkeeping insights."""
    api_key = current_app.config.get('DEEPSEEK_API_KEY')
    if not api_key:
        return None, '未配置 DeepSeek API Key，请先设置环境变量 DEEPSEEK_API_KEY。'

    base_url = (current_app.config.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com').rstrip('/')
    model = current_app.config.get('DEEPSEEK_MODEL') or 'deepseek-v4-flash'
    timeout = int(current_app.config.get('DEEPSEEK_TIMEOUT', 30))

    payload = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': (
                    '你是一名专业的个人财务分析助手。'
                    '请基于用户的记账数据，用简体中文输出实用、具体、克制的分析。'
                    '不要编造不存在的数据。'
                    '输出必须是纯文本，并严格包含以下四段：'
                    '一、总体结论；二、主要消费观察；三、风险提醒；四、可执行建议。'
                    '每段 2 到 4 条，尽量引用金额、类别和趋势。'
                )
            },
            {
                'role': 'user',
                'content': (
                    '请分析下面这段时间的记账数据，并给出可执行建议：\n'
                    f'{json.dumps(dataset, ensure_ascii=False, indent=2)}'
                )
            },
        ],
        'stream': False,
        'temperature': 0.5,
        'max_tokens': 1200,
    }

    response = requests.post(
        f'{base_url}/chat/completions',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()
    choices = data.get('choices') or []
    if not choices:
        raise ValueError('DeepSeek 未返回分析结果')

    message = choices[0].get('message') or {}
    content = (message.get('content') or '').strip()
    if not content:
        raise ValueError('DeepSeek 返回内容为空')

    usage = data.get('usage') or {}
    return {
        'content': content,
        'model': data.get('model') or model,
        'usage': {
            'prompt_tokens': usage.get('prompt_tokens'),
            'completion_tokens': usage.get('completion_tokens'),
            'total_tokens': usage.get('total_tokens'),
        }
    }, None


# ==================== 中文数字解析 ====================
CHINESE_NUMS = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000,
}

def parse_chinese_number(text):
    """解析中文数字表达式, 返回 float 或 None (仅处理中文数字, 不处理阿拉伯数字)"""
    # 处理 "数字+万/千/百" 的组合: "100万" → 1000000, "3千" → 3000
    m = re.search(r'(\d+\.?\d*)\s*(万|千|百)', text)
    if m:
        num = float(m.group(1))
        unit = m.group(2)
        multiplier = CHINESE_NUMS.get(unit, 1)
        return num * multiplier

    # 纯中文数字: 一百二十三, 十二, 三十
    total = 0
    current = 0
    for ch in text:
        val = CHINESE_NUMS.get(ch)
        if val is None:
            continue
        if val >= 10:
            if current == 0:
                current = 1
            total += current * val
            current = 0
        else:
            current = val
    total += current
    return float(total) if total > 0 else None


# ==================== 金额提取 ====================
AMOUNT_PATTERNS = [
    # ￥/¥ 符号 + 数字
    r'[￥¥](\d+\.?\d*)',
    # 数字 + 元/块/毛
    r'(\d+\.?\d*)\s*(?:元|块|毛)',
    # explicit 金额
    r'(?:金额|花费|花了|消费|支付|收入|支出|进账|到账|转账|付了|交了|买了|充值|提现)[^0-9]*(\d+\.?\d*)',
    # 纯数字（兜底，用最长的）
    r'(\d+\.?\d*)',
]

def extract_amount(text):
    """从文本中提取金额, 返回 (amount, raw_match) 或 (None, None)"""
    cn_amount = parse_chinese_number(text)

    all_matches = []
    for pattern in AMOUNT_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            try:
                val = float(m)
                if val > 0 and val < 99999999:
                    all_matches.append(val)
            except ValueError:
                continue

    # 如果有中文数字单位组合（如 "100万"），优先使用
    if re.search(r'\d+\.?\d*\s*(万|千|百)', text):
        if cn_amount and cn_amount > 0:
            return cn_amount, None

    if not all_matches:
        return (cn_amount, None) if cn_amount else (None, None)

    # 如果中文解析结果与某个阿拉伯匹配接近，合并
    if cn_amount:
        for m in all_matches:
            if abs(m - cn_amount) < 0.01:
                return cn_amount, None

    best = max(all_matches)
    return best, best


# ==================== 类型检测 ====================
INCOME_KEYWORDS = [
    '收入', '工资', '奖金', '赚', '收', '进账', '到账', '投资收益',
    '理财', '利息', '分红', '兼职', '外快', '红包', '压岁钱', '礼金',
    '薪水', '薪资', '还款', '报销', '返现', '退款', '押金', '回款',
]

EXPENSE_KEYWORDS = [
    '支出', '花', '买', '消费', '支付', '付', '转账', '缴费',
    '充值', '购物', '餐饮', '吃饭', '交通', '娱乐', '医疗',
    '房租', '水电', '话费', '加油', '打车', '还款', '购物',
    '外卖', '奶茶', '咖啡', '超市', '罚款', '捐赠', '投资',
    '亏', '亏损', '赔',
]

INCOME_VERBS = ['收入', '赚', '挣', '收', '进账', '到账']
EXPENSE_VERBS = ['花', '付', '支出', '消费', '亏', '支付', '付款', '缴费']

def detect_type(text):
    """检测交易类型: income / expense / 不确定则默认 expense"""
    income_score = sum(1 for kw in INCOME_KEYWORDS if kw in text)
    expense_score = sum(1 for kw in EXPENSE_KEYWORDS if kw in text)
    if income_score > expense_score:
        return 'income'
    elif expense_score > income_score:
        return 'expense'
    return 'expense'  # 默认支出


# ==================== 分类匹配 ====================
CATEGORY_KEYWORDS = {
    '餐饮': ['吃饭', '午餐', '晚餐', '早餐', '外卖', '餐厅', '美食', '食堂',
             '火锅', '烧烤', '奶茶', '咖啡', '零食', '水果', '下馆子', '夜宵',
             '快餐', '料理', '寿司', '披萨', '面包', '蛋糕', '甜品', '饮料',
             '茶', '矿泉水'],
    '交通': ['打车', '公交', '地铁', '加油', '停车', '出租车', '高铁', '火车',
             '机票', '汽油', '充电', '过路费', '共享单车', '自行车', '出行',
             '地铁卡', '巴士', '长途', '打车费'],
    '购物': ['购物', '买', '超市', '网购', '淘宝', '京东', '拼多多', '衣服',
             '鞋子', '家电', '日用品', '化妆品', '护肤', '包包', '数码',
             '电子产品', '家居', '饰品', '礼物', '用品'],
    '娱乐': ['娱乐', '电影', '游戏', 'KTV', '旅游', '景点', '门票', '健身',
             '运动', '游泳', '滑雪', '电竞', '桌游', '密室', '游乐园',
             '演唱会', '音乐', '视频', '会员', '充值'],
    '医疗': ['医疗', '医院', '看病', '药', '体检', '挂号', '牙医', '医保',
             '手术', '住院', '中医', '诊所', '药店', '口罩', '消毒'],
    '住房': ['房租', '水电', '物业', '暖气', '房贷', '维修', '家具', '装修',
             '居家', '水费', '电费', '燃气', '网费', '宽带', '保洁', '搬家',
             '家电维修', '管道'],
    '教育': ['教育', '培训', '课程', '书', '学费', '学习', '考试', '报名',
             '网课', '图书', '教材', '文具', '考证', '辅导', '家教', '考研'],
    '通讯': ['话费', '流量', '宽带', '手机', '通讯', '月租', '套餐'],
    '工资': ['工资', '薪水', '薪资', '月薪', '底薪', '工资条', '发工资'],
    '奖金': ['奖金', '年终奖', '绩效', '提成', '分红', '激励'],
    '投资收益': ['投资', '收益', '理财', '基金', '股票', '利息', '分红',
                '债券', '黄金', '期货', '期权'],
    '兼职': ['兼职', '副业', '外快', '零工', '跑腿', '代购', '接单'],
    '红包': ['红包', '压岁钱', '礼金', '份子钱', '随礼'],
    '其他收入': ['其他收入', '杂项', '其他'],
    '其他支出': ['其他支出', '杂项', '其他'],
}

def match_category(text, tx_type, db_categories=None):
    """
    根据文本匹配分类
    1. 优先使用内置关键字映射（精确匹配）
    2. 回退使用数据库中的分类进行字符模糊匹配
    返回 category_name 或 None
    """
    # 1. 内置关键字映射（精确度高）
    builtin_matches = []
    for cat_name, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                builtin_matches.append((cat_name, len(kw)))
    if builtin_matches:
        builtin_matches.sort(key=lambda x: -x[1])
        best_builtin = builtin_matches[0][0]
        # 验证数据库中是否存在且类型匹配
        if db_categories:
            for cat in db_categories:
                if cat.name == best_builtin and cat.type == tx_type:
                    return best_builtin
        # 不在数据库中也返回（后续 type 检测会兜底）
        return best_builtin

    # 2. 数据库分类模糊匹配（兜底）
    if db_categories:
        best_score = 0
        best_db = None
        for cat in db_categories:
            if cat.type != tx_type:
                continue
            score = _keyword_score(cat.name, text)
            if score > best_score:
                best_score = score
                best_db = cat.name
        if best_db and best_score > 0:
            return best_db

    return None


def _keyword_score(cat_name, text):
    """计算分类名称与文本的匹配分数"""
    score = 0
    # 直接命中分类名
    if cat_name in text:
        score += 10
    # 分类名的每个字出现在文本中
    for ch in cat_name:
        if ch in text:
            score += 1
    return score


# ==================== 日期时间提取 ====================
# 日期相对词
DATE_RELATIVE = {
    '今天': 0, '今日': 0,
    '昨天': -1, '昨日': -1,
    '前天': -2, '前日': -2,
    '上周': -7, '上周一': -7, '上周二': -6, '上周三': -5,
    '上周四': -4, '上周五': -3, '上周六': -2, '上周日': -1,
}

def extract_datetime(text):
    """从文本中提取日期和时间, 返回 (date_str, time_str)"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    default_date = now.strftime('%Y-%m-%d')
    default_time = now.strftime('%H:%M:%S')

    date_str = default_date
    time_str = default_time

    # ---- 日期提取 ----
    # 1. 完整日期格式: 2024-01-15, 2024/01/15, 2024年1月15日
    m = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})日?', text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            dt = datetime(y, mo, d)
            if dt.date() <= now.date():
                date_str = dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    else:
        # 2. 月-日: 1月15日, 01/15
        m = re.search(r'(\d{1,2})月(\d{1,2})[日号]?', text)
        if m:
            mo, d = int(m.group(1)), int(m.group(2))
            try:
                dt = datetime(now.year, mo, d)
                if dt.date() > now.date():
                    # 如果是未来的日期，尝试前一年或上个月
                    # 但如果是今年内且没到, 我们仍用今年
                    pass
                date_str = dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

    # 3. 相对日期
    for rel_word, delta_days in DATE_RELATIVE.items():
        if rel_word in text:
            dt = today + timedelta(days=delta_days)
            date_str = dt.strftime('%Y-%m-%d')
            break

    # 4. 星期匹配: 周X / 星期X (只处理过去的)
    weekday_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6}
    m = re.search(r'(?:周|星期)([一二三四五六日天])', text)
    if m and not re.search(r'上[周星期]', text):  # 排除"上周"
        target_wday = weekday_map.get(m.group(1))
        if target_wday is not None:
            current_wday = now.weekday()
            diff = target_wday - current_wday
            if diff > 0:
                diff -= 7  # 取过去最近的那天
            dt = today + timedelta(days=diff)
            date_str = dt.strftime('%Y-%m-%d')

    # ---- 时间提取 ----
    # 1. HH:MM 或 HH:MM:SS
    m = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?', text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        s = int(m.group(3)) if m.group(3) else 0
        if 0 <= h <= 23 and 0 <= mi <= 59:
            time_str = f'{h:02d}:{mi:02d}:{s:02d}'
    else:
        # 2. 下午3点 / 3点半 / 3点30分
        period = 0
        if '下午' in text or '晚上' in text:
            period = 12
        m = re.search(r'(\d{1,2})[点\.](\d{1,2})?[分半]?', text)
        if m:
            h = int(m.group(1))
            if m.group(2):
                mi = int(m.group(2))
            elif '半' in (m.group(0) or ''):
                mi = 30
            else:
                mi = 0
            if period == 12 and h < 12:
                h += 12
            elif h == 12:
                pass
            if 0 <= h <= 23 and 0 <= mi <= 59:
                time_str = f'{h:02d}:{mi:02d}:00'

    return date_str, time_str


# ==================== 备注提取 ====================
def extract_remark(text):
    """从文本中提取备注（去除已识别的日期、金额等结构信息）"""
    # 清理明显的结构化信息
    cleaned = text.strip()
    # 去除金额模式
    cleaned = re.sub(r'[￥¥]\d+\.?\d*', '', cleaned)
    cleaned = re.sub(r'\d+\.?\d*\s*(?:元|块|毛)', '', cleaned)
    # 去除日期模式
    cleaned = re.sub(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?', '', cleaned)
    cleaned = re.sub(r'\d{1,2}月\d{1,2}[日号]?', '', cleaned)
    cleaned = re.sub(r'(?:今天|昨天|前天|上周)', '', cleaned)
    cleaned = re.sub(r'(?:周|星期)[一二三四五六日天]', '', cleaned)
    # 去除时间模式
    cleaned = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?', '', cleaned)
    cleaned = re.sub(r'(?:下午|晚上|早上|上午)\d{1,2}[点\.]\d{1,2}?[分半]?', '', cleaned)
    # 去除分类/类型关键词词头
    cleaned = re.sub(r'^(?:收入|支出|花费|消费|支付|转账|买了|交了|付了|充值)\s*', '', cleaned)
    cleaned = cleaned.strip()
    # 如果清理后为空，返回原始文本的前20字
    if len(cleaned) < 2:
        return text[:30]
    return cleaned[:50]


# ==================== 区块完整性检查 ====================
def check_amount_reasonableness(amount, category, tx_type):
    """金额合理性检查, 返回 (is_reasonable, warning_message)"""
    if amount <= 0:
        return False, '金额必须大于0'

    if amount > 99999999.99:
        return False, '金额超出系统限制'

    # 按类型和分类的合理范围检查
    THRESHOLDS = {
        'expense': {
            '餐饮': 5000, '交通': 10000, '购物': 50000, '娱乐': 20000,
            '医疗': 100000, '住房': 100000, '教育': 100000, '通讯': 2000,
        },
        'income': {},
    }

    threshold = THRESHOLDS.get(tx_type, {}).get(category, 0)
    if threshold and amount > threshold:
        ratio = amount / threshold
        if ratio > 10:
            return False, f'该{category}交易金额 ¥{amount:.2f} 异常偏高，请确认'
        elif ratio > 3:
            return True, f'提示：该{category}交易金额 ¥{amount:.2f} 偏高，是否确认？'

    return True, None


def check_duplicate(amount, category, date_str, user_id):
    """重复交易检测, 返回 (is_dup, message)"""
    db, Transaction, _, _, _ = _import_models()

    # 检查相同日期、相同分类、相同金额的交易
    same_day_tx = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date == date_str,
        Transaction.category == category,
        Transaction.amount == amount,
    ).count()

    if same_day_tx > 0:
        return True, f'检测到重复账单：当天已有 {same_day_tx} 笔相同的「{category} ¥{amount:.2f}」记录'

    # 检查 3 天内同类金额（误差 5% 以内）
    three_days = datetime.strptime(date_str, '%Y-%m-%d') - timedelta(days=3)
    amount_low = amount * 0.95
    amount_high = amount * 1.05

    nearby = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= three_days.strftime('%Y-%m-%d'),
        Transaction.date <= date_str,
        Transaction.category == category,
        Transaction.amount.between(amount_low, amount_high),
        Transaction.id != None,
    ).count()

    if nearby > 0:
        return True, f'近期已有 {nearby} 笔类似交易（¥{amount_low:.2f} ~ ¥{amount_high:.2f}），请确认是否重复'

    return False, None


# ==================== 多交易拆分 ====================
AMOUNT_PATTERN_ALL = re.compile(
    r'[￥¥](\d+\.?\d*)'
    r'|(\d+\.?\d*)\s*(?:元|块|毛)'
    r'|(?:金额|花费|花了|消费|支付|收入|支出|进账|到账|转账|付了|交了|买了|充值|提现)[^0-9]*(\d+\.?\d*)'
    r'|(\d+\.?\d*)'
)

CN_UNIT_PATTERN = re.compile(r'(\d+\.?\d*)\s*(万|千|百)')

def find_amounts_with_positions(text):
    """返回 [(amount, start_pos, end_pos), ...] 所有金额及其在文本中的位置"""
    results = []
    seen_spans = set()

    for m in AMOUNT_PATTERN_ALL.finditer(text):
        for g_idx in range(1, m.lastindex + 1):
            val_str = m.group(g_idx)
            if val_str is not None:
                try:
                    val = float(val_str)
                    if 0 < val < 99999999:
                        span = (m.start(), m.end())
                        if span not in seen_spans:
                            seen_spans.add(span)
                            results.append((val, m.start(), m.end()))
                except ValueError:
                    continue
                break

    # 中文单位: "100万" → 1000000
    for m in CN_UNIT_PATTERN.finditer(text):
        num = float(m.group(1))
        unit = m.group(2)
        multiplier = CHINESE_NUMS.get(unit, 1)
        val = num * multiplier
        span = (m.start(), m.end())
        if span not in seen_spans and 0 < val < 99999999:
            seen_spans.add(span)
            results.append((val, m.start(), m.end()))

    # 中文纯数字
    cn_val = parse_chinese_number(text)
    if cn_val and cn_val > 0:
        already = any(abs(r[0] - cn_val) < 0.01 for r in results)
        if not already:
            results.append((cn_val, 0, len(text)))

    results.sort(key=lambda x: x[1])
    # 去重（同位置附近的仅保留最大金额）
    deduped = []
    for r in results:
        if deduped and abs(r[1] - deduped[-1][1]) < 3:
            if r[0] > deduped[-1][0]:
                deduped[-1] = r
        else:
            deduped.append(r)
    return deduped


def detect_segment_type(text):
    """单段文本的类型检测, 返回 income / expense"""
    inc = sum(1 for kw in INCOME_KEYWORDS if kw in text)
    exp = sum(1 for kw in EXPENSE_KEYWORDS if kw in text)

    # 在金额附近的动词权重更高
    amount_positions = find_amounts_with_positions(text)
    if amount_positions:
        avg_pos = sum(p[1] for p in amount_positions) / len(amount_positions)
        before = text[:int(avg_pos)]
        after = text[int(avg_pos):]
        inc_b = sum(1 for kw in INCOME_VERBS if kw in before)
        exp_b = sum(1 for kw in EXPENSE_VERBS if kw in before)
        inc += inc_b * 2
        exp += exp_b * 2

    if inc > exp:
        return 'income'
    elif exp > inc:
        return 'expense'
    return 'expense'


def split_transactions(text):
    """
    将含多笔交易的文本拆分为独立交易文本列表
    例如: "今天亏1000元然后又赚了200" → ["今天亏1000元", "赚了200"]
    """
    amounts = find_amounts_with_positions(text)

    # 仅 0 或 1 个金额 → 单笔
    if len(amounts) <= 1:
        return [text]

    # 如果有明确的分隔词, 优先按分隔词切分
    separators = ['然后又', '然后又', '接着又', '后来又', '另外还',
                  '同时还', '并且还', '而且还', '另外', '还有', '此外', '以及']
    remaining = text
    segments = []
    for sep in separators:
        if sep in remaining:
            before, after = remaining.split(sep, 1)
            b_amts = find_amounts_with_positions(before)
            a_amts = find_amounts_with_positions(after)
            if b_amts and a_amts:
                segments.append(before.strip().rstrip('，。,.;；、'))
                remaining = after

    if segments and remaining.strip():
        remaining = remaining.strip().rstrip('，。,.;；、')
        if remaining:
            segments.append(remaining)
        return segments

    # 按标点符号拆分 (仅当每段都有金额)
    parts = re.split(r'[，,;；。]', text)
    parts = [p.strip() for p in parts if p.strip()]
    parts = [(p, find_amounts_with_positions(p)) for p in parts]
    parts = [(p, a) for p, a in parts if a]  # 只保留有金额的段
    if len(parts) >= 2:
        return [p for p, _ in parts]

    # 兜底: 在金额之间的中间位置切分
    if amounts:
        split_pos = (amounts[0][2] + amounts[1][1]) // 2
        seg1 = text[:split_pos].strip().rstrip('，。,.;；、')
        seg2 = text[split_pos:].strip().rstrip('，。,.;；、')
        return [s for s in [seg1, seg2] if s]

    return [text]


def parse_single_transaction(text, all_categories, user_id):
    """解析单段文本为一笔交易, 返回 parsed dict + warnings"""
    tx_type = detect_segment_type(text)

    amount, _ = extract_amount(text)
    if amount is None:
        return None

    category_name = match_category(text, tx_type, all_categories)
    if not category_name:
        fallback_name = '其他收入' if tx_type == 'income' else '其他支出'
        for cat in all_categories:
            if cat.name == fallback_name and cat.type == tx_type:
                category_name = cat.name
                break
        if not category_name:
            category_name = fallback_name

    date_str, time_str = extract_datetime(text)
    remark = extract_remark(text)

    amount_warnings = []
    _, warn_msg = check_amount_reasonableness(amount, category_name, tx_type)
    if warn_msg:
        amount_warnings.append(warn_msg)

    dup_warnings = []
    _, dup_msg = check_duplicate(amount, category_name, date_str, user_id)
    if dup_msg:
        dup_warnings.append(dup_msg)

    return {
        'type': tx_type,
        'amount': round(amount, 2),
        'category': category_name,
        'date': date_str,
        'time': time_str,
        'remark': remark,
        'currency': 'CNY',
        '_warnings': {
            'amount': amount_warnings,
            'duplicate': dup_warnings,
            'all': amount_warnings + dup_warnings,
        },
    }


# ==================== 主解析入口 ====================
@smart_bp.route('/parse', methods=['POST'])
def smart_parse():
    """
    智能解析文本内容为账单信息
    输入: { text: "今天中午吃饭花了35块" }
    输出: 单笔 → { parsed: {...} }; 多笔 → { parsed_list: [{...}, ...], multi: true }
    """
    try:
        db, Transaction, Category, Account, _ = _import_models()
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        data = request.get_json()
        if not data or not data.get('text'):
            return jsonify({'success': False, 'message': '请输入内容'}), 400

        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'message': '内容不能为空'}), 400

        all_categories = Category.query.all()

        # 尝试拆分为多笔交易
        segments = split_transactions(text)

        # 解析每段
        parsed_list = []
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            result = parse_single_transaction(seg, all_categories, user_id)
            if result:
                parsed_list.append(result)

        if not parsed_list:
            return jsonify({'success': False, 'message': '无法识别金额，请直接输入数字金额'}), 400

        # 构建响应
        if len(parsed_list) == 1:
            p = parsed_list[0]
            w = p.pop('_warnings')
            result = {
                'success': True,
                'multi': False,
                'parsed': p,
                'warnings': w,
                'has_warnings': len(w['all']) > 0,
            }
        else:
            all_warnings = []
            for p in parsed_list:
                w = p.pop('_warnings')
                all_warnings.extend(w['all'])
            result = {
                'success': True,
                'multi': True,
                'parsed_list': parsed_list,
                'total': len(parsed_list),
                'warnings': {'all': all_warnings},
                'has_warnings': len(all_warnings) > 0,
            }

        logger.info(f'智能解析: user={user_id}, segments={len(parsed_list)}, text="{text[:40]}..."')
        return jsonify(result)

    except Exception as e:
        logger.error(f'智能解析失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '解析失败，请稍后重试'}), 500


@smart_bp.route('/confirm', methods=['POST'])
def smart_confirm():
    """
    用户确认或修改后的智能账单 - 创建交易
    输入: { type, amount, category, date, time, remark, account_id, currency }
    """
    try:
        db, Transaction, Category, Account, _ = _import_models()
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400

        # === 复用现有 /api/transactions POST 的校验逻辑 ===
        tx_type = data.get('type')
        if tx_type not in ['income', 'expense']:
            return jsonify({'success': False, 'message': '交易类型必须是 income 或 expense'}), 400

        try:
            amount = float(data.get('amount', 0))
            if amount <= 0:
                return jsonify({'success': False, 'message': '金额必须大于0'}), 400
            if amount > 99999999.99:
                return jsonify({'success': False, 'message': '金额超出限制'}), 400
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '金额格式不正确'}), 400

        currency = data.get('currency', 'CNY').upper()
        from app import CURRENCY_NAMES
        if currency not in CURRENCY_NAMES and currency != 'CNY':
            return jsonify({'success': False, 'message': f'不支持的币种: {currency}'}), 400

        from app import get_exchange_rate
        exchange_rate = None
        tx_amount = amount
        tx_original_amount = None

        if currency == 'CNY':
            tx_amount = amount
        else:
            tx_original_amount = amount
            rate = get_exchange_rate(currency, 'CNY')
            if rate is None:
                return jsonify({'success': False, 'message': f'获取 {currency} 汇率失败'}), 502
            exchange_rate = round(rate, 6)
            tx_amount = round(amount * rate, 2)

        category_name = data.get('category', '').strip()
        if not category_name:
            return jsonify({'success': False, 'message': '分类不能为空'}), 400
        category = Category.query.filter_by(name=category_name, type=tx_type).first()
        if not category:
            return jsonify({'success': False, 'message': f'分类「{category_name}」不存在或类型不匹配'}), 400

        tx_date = data.get('date', '').strip()
        now = datetime.now()
        if not tx_date:
            tx_date = now.strftime('%Y-%m-%d')
        else:
            try:
                parsed_date = datetime.strptime(tx_date, '%Y-%m-%d')
                if parsed_date.date() > now.date():
                    return jsonify({'success': False, 'message': '日期不能晚于今天'}), 400
            except ValueError:
                return jsonify({'success': False, 'message': '日期格式不正确'}), 400

        tx_time = data.get('time', '').strip()
        if not tx_time:
            tx_time = now.strftime('%H:%M:%S')
        else:
            try:
                datetime.strptime(tx_time, '%H:%M:%S')
            except ValueError:
                tx_time = now.strftime('%H:%M:%S')

        account_id = data.get('account_id')
        account = None
        from app import get_current_ledger_id
        current_ledger_id = get_current_ledger_id()
        if account_id:
            account = Account.query.filter_by(id=account_id).first()
            if not account or (current_ledger_id and account.ledger_id != current_ledger_id):
                return jsonify({'success': False, 'message': '账户不存在'}), 400
        else:
            if current_ledger_id:
                account = Account.query.filter_by(ledger_id=current_ledger_id).first()
            else:
                account = Account.query.filter_by(user_id=user_id).first()
            if not account:
                account = Account(name='默认账户', balance=0, account_type='cash', user_id=user_id, ledger_id=current_ledger_id)
                db.session.add(account)
                db.session.flush()
            account_id = account.id

        # 创建交易
        tx = Transaction(
            type=tx_type,
            amount=tx_amount,
            category=category_name,
            date=tx_date,
            time=tx_time,
            remark=data.get('remark', '').strip(),
            account_id=account_id,
            user_id=user_id,
            ledger_id=current_ledger_id,
            currency=currency,
            original_amount=tx_original_amount,
            exchange_rate=exchange_rate,
        )
        db.session.add(tx)

        if tx_type == 'income':
            account.balance = float(account.balance) + tx_amount
        else:
            account.balance = float(account.balance) - tx_amount

        db.session.flush()

        log_money_change = _get_log_helper()
        log_money_change(
            user_id=user_id,
            action_type='create',
            entity_type='transaction',
            entity_id=tx.id,
            amount_change=tx_amount if tx_type == 'income' else -tx_amount,
            account_id=account_id,
            ledger_id=current_ledger_id,
            description=f'智能记账创建{"收入" if tx_type == "income" else "支出"} ￥{tx_amount:.2f} - {category_name}'
        )

        db.session.commit()
        from app import get_balance
        balance = get_balance()
        logger.info(f'智能记账确认: {tx_type} ¥{tx_amount} - {category_name}')

        return jsonify({
            'success': True,
            'message': '交易添加成功',
            'balance': balance,
            'account_balance': float(account.balance),
            'transaction_id': tx.id,
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f'智能记账确认失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '添加交易失败'}), 500


@smart_bp.route('/deepseek-analysis', methods=['GET'])
def deepseek_analysis():
    """Use DeepSeek to analyze the current user's bookkeeping data with caching."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        period = request.args.get('period', 'month')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        dataset = _build_analysis_dataset(user_id, period, start_date, end_date)
        if not dataset:
            return jsonify({'success': False, 'message': '当前时间范围内没有可供分析的记账数据'}), 404

        db, _, _, _, AIAnalysis = _import_models()

        # 检查缓存：查找未删除且在当前时间范围内的最新分析
        if not force_refresh:
            cached_analysis = AIAnalysis.query.filter(
                AIAnalysis.user_id == user_id,
                AIAnalysis.period == period,
                AIAnalysis.start_date == dataset['start_date'],
                AIAnalysis.end_date == dataset['end_date'],
                AIAnalysis.is_deleted == False
            ).order_by(AIAnalysis.created_at.desc()).first()

            if cached_analysis:
                # 检查缓存是否过期（24小时内）
                cache_age = datetime.now() - cached_analysis.created_at
                if cache_age < timedelta(hours=24):
                    logger.info(f'使用缓存的 AI 分析结果，用户ID: {user_id}')
                    return jsonify({
                        'success': True,
                        'period': dataset['period'],
                        'start_date': dataset['start_date'],
                        'end_date': dataset['end_date'],
                        'summary': dataset['summary'],
                        'analysis': cached_analysis.analysis_content,
                        'model': cached_analysis.model_used,
                        'usage': {
                            'prompt_tokens': cached_analysis.prompt_tokens,
                            'completion_tokens': cached_analysis.completion_tokens,
                            'total_tokens': cached_analysis.total_tokens,
                        },
                        'cached': True,
                        'created_at': cached_analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'analysis_id': cached_analysis.id,
                    })

        # 调用 DeepSeek API
        analysis, config_error = _call_deepseek_analysis(dataset)
        if config_error:
            return jsonify({'success': False, 'message': config_error}), 503

        # 保存分析结果到数据库
        new_analysis = AIAnalysis(
            user_id=user_id,
            period=dataset['period'],
            start_date=dataset['start_date'],
            end_date=dataset['end_date'],
            analysis_content=analysis['content'],
            model_used=analysis['model'],
            prompt_tokens=analysis['usage'].get('prompt_tokens', 0),
            completion_tokens=analysis['usage'].get('completion_tokens', 0),
            total_tokens=analysis['usage'].get('total_tokens', 0),
        )
        db.session.add(new_analysis)
        db.session.commit()

        logger.info(f'AI 分析结果已保存，用户ID: {user_id}, 分析ID: {new_analysis.id}')

        return jsonify({
            'success': True,
            'period': dataset['period'],
            'start_date': dataset['start_date'],
            'end_date': dataset['end_date'],
            'summary': dataset['summary'],
            'analysis': analysis['content'],
            'model': analysis['model'],
            'usage': analysis['usage'],
            'cached': False,
            'analysis_id': new_analysis.id,
        })
    except requests.HTTPError as e:
        logger.error(f'DeepSeek API HTTP error: {e}', exc_info=True)
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text if e.response is not None else str(e)
        return jsonify({
            'success': False,
            'message': 'DeepSeek 分析请求失败',
            'detail': detail,
        }), 502
    except requests.RequestException as e:
        logger.error(f'DeepSeek API request failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '无法连接到 DeepSeek 服务，请稍后重试'}), 502
    except Exception as e:
        logger.error(f'DeepSeek analysis failed: {e}', exc_info=True)
        return jsonify({'success': False, 'message': 'AI 分析失败，请稍后重试'}), 500


@smart_bp.route('/ai-analysis', methods=['GET'])
def get_ai_analysis_history():
    """获取用户的 AI 分析历史记录"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        db, _, _, _, AIAnalysis = _import_models()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        period = request.args.get('period')

        query = AIAnalysis.query.filter(
            AIAnalysis.user_id == user_id,
            AIAnalysis.is_deleted == False
        )

        if period:
            query = query.filter(AIAnalysis.period == period)

        pagination = query.order_by(AIAnalysis.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        analyses = []
        for analysis in pagination.items:
            analyses.append({
                'id': analysis.id,
                'period': analysis.period,
                'start_date': analysis.start_date,
                'end_date': analysis.end_date,
                'model': analysis.model_used,
                'usage': {
                    'prompt_tokens': analysis.prompt_tokens,
                    'completion_tokens': analysis.completion_tokens,
                    'total_tokens': analysis.total_tokens,
                },
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return jsonify({
            'success': True,
            'analyses': analyses,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
            },
        })
    except Exception as e:
        logger.error(f'获取 AI 分析历史失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '获取历史记录失败'}), 500


@smart_bp.route('/ai-analysis/<int:analysis_id>', methods=['GET'])
def get_ai_analysis_detail(analysis_id):
    """获取指定 AI 分析的详细信息"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        db, _, _, _, AIAnalysis = _import_models()

        analysis = AIAnalysis.query.filter(
            AIAnalysis.id == analysis_id,
            AIAnalysis.user_id == user_id,
            AIAnalysis.is_deleted == False
        ).first()

        if not analysis:
            return jsonify({'success': False, 'message': '未找到该分析结果'}), 404

        return jsonify({
            'success': True,
            'analysis': {
                'id': analysis.id,
                'period': analysis.period,
                'start_date': analysis.start_date,
                'end_date': analysis.end_date,
                'content': analysis.analysis_content,
                'model': analysis.model_used,
                'usage': {
                    'prompt_tokens': analysis.prompt_tokens,
                    'completion_tokens': analysis.completion_tokens,
                    'total_tokens': analysis.total_tokens,
                },
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            },
        })
    except Exception as e:
        logger.error(f'获取 AI 分析详情失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '获取分析详情失败'}), 500


@smart_bp.route('/ai-analysis/<int:analysis_id>', methods=['DELETE'])
def delete_ai_analysis(analysis_id):
    """删除指定的 AI 分析结果（软删除）"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        db, _, _, _, AIAnalysis = _import_models()

        analysis = AIAnalysis.query.filter(
            AIAnalysis.id == analysis_id,
            AIAnalysis.user_id == user_id,
            AIAnalysis.is_deleted == False
        ).first()

        if not analysis:
            return jsonify({'success': False, 'message': '未找到该分析结果'}), 404

        # 软删除
        analysis.is_deleted = True
        db.session.commit()

        logger.info(f'AI 分析结果已删除，用户ID: {user_id}, 分析ID: {analysis_id}')

        return jsonify({
            'success': True,
            'message': '分析结果已删除',
        })
    except Exception as e:
        logger.error(f'删除 AI 分析失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '删除失败'}), 500


@smart_bp.route('/ai-analysis', methods=['DELETE'])
def delete_multiple_ai_analysis():
    """批量删除 AI 分析结果"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '未登录'}), 401

        data = request.get_json()
        if not data or 'analysis_ids' not in data:
            return jsonify({'success': False, 'message': '请提供要删除的分析ID列表'}), 400

        analysis_ids = data['analysis_ids']
        if not isinstance(analysis_ids, list):
            return jsonify({'success': False, 'message': 'analysis_ids 必须是数组'}), 400

        db, _, _, _, AIAnalysis = _import_models()

        deleted_count = AIAnalysis.query.filter(
            AIAnalysis.id.in_(analysis_ids),
            AIAnalysis.user_id == user_id,
            AIAnalysis.is_deleted == False
        ).update({'is_deleted': True})

        db.session.commit()

        logger.info(f'批量删除 AI 分析结果，用户ID: {user_id}, 删除数量: {deleted_count}')

        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 条分析记录',
            'deleted_count': deleted_count,
        })
    except Exception as e:
        logger.error(f'批量删除 AI 分析失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': '删除失败'}), 500
