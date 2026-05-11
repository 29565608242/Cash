# 线上记账系统

基于 Flask 的在线记账管理系统，支持多用户、多账本、预算管理、报销核销、借贷管理、数据导入导出和智能记账辅助。

## 技术栈

- **后端**: Flask 3.0 + Flask-SQLAlchemy
- **数据库**: MySQL 8.0+ (PyMySQL)
- **前端**: Jinja2 + Bootstrap 5 + ECharts 5
- **数据处理**: openpyxl, chardet
- **AI 辅助**: DeepSeek API
- **小程序**: uni-app (微信小程序/H5)

## 项目结构

```
├── app.py                       # 应用入口
├── run.py                       # 开发启动脚本
├── config.py                    # 配置管理
├── db_test.sql                  # 数据库初始化脚本（参考用）
├── requirements.txt
├── miniprogram/                 # uni-app 小程序
├── cash_app/                    # 核心应用包
│   ├── __init__.py
│   ├── app_state.py             # Flask/SQLAlchemy 实例
│   ├── models.py                # 数据模型（15个表）
│   ├── routes_base.py           # 基础路由（登录/注册/管理后台）
│   ├── routes_transactions.py   # 交易/报销/用户管理 API
│   ├── routes_finance.py        # 财务路由（预算/借贷/周期账单）
│   ├── routes_ledgers.py        # 多账本路由
│   ├── routes_miniapp.py        # 小程序 API
│   ├── auth.py                  # 认证与权限
│   ├── core.py                  # 核心工具函数
│   ├── support.py               # 查询过滤/余额计算
│   ├── bootstrap.py             # 启动初始化
│   └── init_db.py               # 数据库迁移逻辑
├── blueprints/
│   ├── import_export.py         # 数据导入导出（Blueprint）
│   └── smart_bookkeeping.py     # 智能记账（Blueprint）
├── templates/                   # Jinja2 页面模板
│   ├── admin.html               # 管理后台
│   ├── index.html               # 用户首页
│   ├── reports.html             # 财务报表
│   └── ...
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── avatars/
└── data/                        # 运行时数据目录
    ├── uploads/
    ├── exports/
    └── backups/
```

## 快速开始

### 1. 环境准备

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. 数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入结构（或跳过，应用启动时会自动建表）
mysql -u root -p db_test < db_test.sql
```

### 3. 配置

编辑 `config.py`：
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:密码@localhost:3306/db_test'
```

### 4. 启动

```bash
python run.py        # 开发模式，默认 http://localhost:8080
```

### 5. 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | user | user123 |

## 管理后台

管理员登录后自动进入后台，功能包括：

- **全平台统计**: 总收入/支出/余额，今日收支
- **各用户数据统计**: 每个普通用户的交易笔数、收支汇总（不含管理员）
- **数据分析看板**: 分类分布饼图、月度趋势折线图、用户对比柱状图
- **全平台交易记录**: 所有用户的全部交易，支持按用户/类型/时间筛选
- **用户管理**: 搜索、重置密码、删除空账号

> 管理员自身的记账数据不计入平台统计，后台仅展示普通用户的数据。

## 功能特性

- **多账本**: 支持创建多个账本，邀请成员协作记账
- **预算管理**: 月度总预算 + 分类预算，超支自动预警
- **报销核销**: 支出标记为待报销，创建报销收入自动核销
- **借贷管理**: 记录借入/借出，跟踪还款状态
- **多币种**: 支持多种货币记账，自动汇率换算
- **周期账单**: 日/周/月/年定期账单自动生成
- **数据导入导出**: Excel/CSV 导入导出，大数据异步处理
- **AI 智能记账**: DeepSeek 驱动，自然语言记账、数据分析、异常检测
- **资金变动日志**: 完整的资金操作审计追踪
- **数据备份**: 定期自动备份

## miniprogram (uni-app 小程序)

小程序基于 uni-app 开发，位于 `miniprogram/` 目录，对接 Flask 后端 API。

### 小程序页面

- **认证**: 登录、注册
- **首页看板**: 收支概览、图表
- **交易管理**: 交易列表、添加、详情、编辑
- **账户管理**: 多账户查看
- **账本与成员**: 账本切换、成员管理
- **预算管理**: 预算设定与进度跟踪
- **借贷管理**: 借入/借出记录
- **报销管理**: 报销核销流程
- **周期账单**: 周期规则管理
- **报表统计**: 分类分布、月度趋势
- **智能记账**: 自然语言记账、AI 分析
- **个人中心**: 资料修改、密码变更

### 联调步骤

1. 启动 Flask 后端（默认 `http://127.0.0.1:8080`）
2. 用 HBuilderX 导入 `miniprogram/`
3. 运行到微信开发者工具或 Web 预览进行调试
4. 如果后端地址不同，修改 `miniprogram/services/api.js` 中的 `BASE_URL`

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| FLASK_ENV | development | 运行环境 |
| HOST | 0.0.0.0 | 监听地址 |
| PORT | 8080 | 监听端口 |
| SECRET_KEY | dev-secret-key-... | 会话密钥 |
| MAX_TRANSACTIONS_DISPLAY | 10000 | 最大显示条数 |
| DEEPSEEK_API_KEY | - | AI 记账 API 密钥 |
| DEEPSEEK_BASE_URL | https://api.deepseek.com | DeepSeek API 地址 |
| DEEPSEEK_MODEL | deepseek-v4-flash | DeepSeek 模型名称 |
| BACKUP_ENABLED | true | 是否启用自动备份 |
| SMTP_SERVER | smtp.qq.com | 邮件服务器 |

## 数据库说明

应用启动时自动执行以下操作：
1. `db.create_all()` 创建所有不存在的表
2. 自动执行字段迁移（为旧表补充新字段）
3. 初始化默认分类和默认用户

共 15 张表：users, categories, accounts, transactions, budgets, budget_category_items, export_tasks, file_uploads, ledgers, ledger_members, invite_codes, loans, ai_analysis, recurring_rules, money_change_logs。
