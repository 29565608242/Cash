import json
import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from flask import jsonify
from werkzeug.exceptions import HTTPException

from .app_state import DATA_FILE, app, config

def setup_logging():
    """配置日志系统"""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    # 创建日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（带日志轮转）
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 配置 Flask 日志
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    app.logger.info(f"{config.APP_NAME} 启动成功")
    app.logger.info(f"数据文件: {DATA_FILE}")
    app.logger.info(f"日志级别: {config.LOG_LEVEL}")


setup_logging()


# ==================== 数据管理 ====================
def init_data_file():
    """初始化数据文件"""
    if not os.path.exists(DATA_FILE):
        default_data = {
            "transactions": [],
            "balance": 0,
            "categories": config.DEFAULT_CATEGORIES
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        app.logger.info(f"已创建新的数据文件: {DATA_FILE}")


def load_data():
    """读取数据"""
    try:
        init_data_file()
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        app.logger.error(f"JSON 解析错误: {e}")
        # 备份损坏的文件
        backup_file = f"{DATA_FILE}.error.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        os.rename(DATA_FILE, backup_file)
        app.logger.warning(f"已备份损坏文件到: {backup_file}")
        init_data_file()
        return load_data()
    except Exception as e:
        app.logger.error(f"读取数据失败: {e}")
        raise


def save_data(data):
    """保存数据（带备份）"""
    try:
        # 先保存到临时文件
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 验证临时文件可以正常读取
        with open(temp_file, 'r', encoding='utf-8') as f:
            json.load(f)
        
        # 替换原文件
        if os.path.exists(DATA_FILE):
            os.replace(temp_file, DATA_FILE)
        else:
            os.rename(temp_file, DATA_FILE)
        
        app.logger.debug("数据保存成功")
    except Exception as e:
        app.logger.error(f"保存数据失败: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise


# ==================== 汇率服务 ====================
# 默认汇率（API 不可用时兜底）
DEFAULT_EXCHANGE_RATES = {
    'USD': 7.24, 'EUR': 7.87, 'GBP': 9.15, 'JPY': 0.048,
    'HKD': 0.93, 'KRW': 0.0054, 'SGD': 5.38, 'THB': 0.20,
    'TWD': 0.22, 'AUD': 4.82, 'CAD': 5.28, 'MYR': 1.55,
}

# 币种名称映射
CURRENCY_NAMES = {
    'CNY': '人民币', 'USD': '美元', 'EUR': '欧元', 'GBP': '英镑',
    'JPY': '日元', 'HKD': '港币', 'KRW': '韩元', 'SGD': '新加坡元',
    'THB': '泰铢', 'TWD': '台币', 'AUD': '澳元', 'CAD': '加元', 'MYR': '马币',
}

# 币种符号映射
CURRENCY_SYMBOLS = {
    'CNY': '￥', 'USD': '$', 'EUR': '€', 'GBP': '￡',
    'JPY': '￥', 'HKD': 'HK$', 'KRW': '?', 'SGD': 'S$',
    'THB': '?', 'TWD': 'NT$', 'AUD': 'A$', 'CAD': 'C$', 'MYR': 'RM',
}

# 汇率缓存 {cache_key: (rate, timestamp)}
_exchange_rate_cache = {}

def get_exchange_rate(from_currency, to_currency='CNY'):
    """获取实时汇率，优先缓存，其次 API,最后默认汇率"""
    if from_currency == to_currency:
        return 1.0

    cache_key = f"{from_currency}_{to_currency}"

    # 检查缓存（5分钟有效）
    if cache_key in _exchange_rate_cache:
        rate, ts = _exchange_rate_cache[cache_key]
        if time.time() - ts < 300:
            return rate

    # 调用免费汇率 API
    try:
        url = f"https://open.er-api.com/v6/latest/{from_currency}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get('result') == 'success':
            rate = data['rates'].get(to_currency)
            if rate:
                _exchange_rate_cache[cache_key] = (rate, time.time())
                app.logger.info(f"获取实时汇率: 1 {from_currency} = {rate} {to_currency}")
                return rate
    except Exception as e:
        app.logger.warning(f"汇率 API 请求失败: {e}")

    # API 失败，使用默认汇率
    rate = DEFAULT_EXCHANGE_RATES.get(from_currency)
    if rate:
        app.logger.info(f"使用默认汇率: 1 {from_currency} = {rate} {to_currency}")
        return rate

    app.logger.error(f"无法获取汇率: {from_currency} -> {to_currency}")
    return None


# ==================== 错误处理 ====================
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理"""
    # 处理 HTTP 异常
    if isinstance(e, HTTPException):
        response = {
            "success": False,
            "error": e.name,
            "message": e.description,
            "status_code": e.code
        }
        return jsonify(response), e.code
    
    # 处理其他异常
    app.logger.error(f"未处理的异常: {str(e)}", exc_info=True)
    response = {
        "success": False,
        "error": "Internal Server Error",
        "message": "服务器内部错误，请稍后重试",
        "status_code": 500
    }
    return jsonify(response), 500


@app.errorhandler(404)
def not_found(e):
    """404 错误处理"""
    return jsonify({
        "success": False,
        "error": "Not Found",
        "message": "请求的资源不存在",
        "status_code": 404
    }), 404


@app.errorhandler(400)
def bad_request(e):
    """400 错误处理"""
    return jsonify({
        "success": False,
        "error": "Bad Request",
        "message": str(e.description) if e.description else "请求参数错误",
        "status_code": 400
    }), 400


# ==================== 健康检查 ====================
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 检查数据文件是否可读
        data = load_data()
        
        return jsonify({
            "status": "healthy",
            "app_name": config.APP_NAME,
            "timestamp": datetime.now().isoformat(),
            "data_file": os.path.exists(DATA_FILE),
            "transactions_count": len(data.get('transactions', [])),
            "balance": data.get('balance', 0)
        }), 200
    except Exception as e:
        app.logger.error(f"健康检查失败: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


@app.route('/api/info', methods=['GET'])
def api_info():
    """API 信息端点"""
    return jsonify({
        "app_name": config.APP_NAME,
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "index": "/",
            "admin": "/admin",
            "transactions": "/api/transactions",
            "categories": "/api/categories",
            "accounts": "/api/accounts",
            "reports": "/api/reports/<period>",
            "reports_advanced": "/api/reports/advanced"
        }
    })


# ==================== 页面路由 ====================
# 登录路由

