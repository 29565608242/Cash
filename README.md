# 线上记账管理系统

一个基于 Flask、MySQL 和 uni-app 的多端记账系统，提供 Web 管理端、REST API 和微信小程序端。系统围绕个人记账与共享账本协作设计，支持交易流水、账户余额、预算、借贷、报销、周期账单、数据导入导出、文本智能记账和 AI 财务分析。

## 项目特性

- 多端使用：Web 端用于完整管理，小程序端用于移动记账和日常查看，后端 API 统一提供数据能力。
- 多用户与权限：支持普通用户、管理员、账本所有者、账本管理员、编辑者和查看者。
- 个人模式与共享账本：个人模式使用独立个人数据；共享账本支持创建、切换、成员管理、邀请码加入和角色控制。
- 邀请协作：邀请码加入账本的新成员默认角色为 `editor`，可直接参与记账；管理员可后续调整为 `viewer` 或 `manager`。
- 完整记账能力：支持收入、支出、转账、预付款、附件、定位、AA 分摊、付款人、统计开关和多币种换算。
- 账户余额联动：交易、借贷、还款、导入等操作会同步维护账户余额，并写入资金变动日志。
- 财务扩展：支持预算、借入借出、报销核销、周期账单自动生成、报表统计和高级筛选。
- 数据工具：支持 CSV / Excel 导入、字段映射、异步导出、导出下载和邮件发送。
- 智能能力：智能记账基于文本解析，不使用 OCR；AI 财务分析可按周期调用 DeepSeek 生成分析建议。
- 管理后台：管理员可查看平台概览、用户统计、交易数据，并可重置密码或删除普通用户及其相关数据。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | Python, Flask 3, Flask-SQLAlchemy, Flask-CORS, Werkzeug |
| 数据库 | MySQL, PyMySQL |
| Web 前端 | Jinja2, 原生 JavaScript, Bootstrap, ECharts |
| 小程序端 | uni-app, Vue 3, Sass, Vite |
| 文件处理 | openpyxl, chardet, CSV |
| 外部服务 | DeepSeek API, SMTP, 汇率接口 |

## 目录结构

```text
.
├── run.py                         # Flask 应用启动入口
├── config.py                      # 应用配置、目录配置和第三方服务配置
├── requirements.txt               # Python 依赖
├── db_test.sql                    # 数据库结构参考
├── cash_app/
│   ├── app_state.py               # Flask / SQLAlchemy 实例初始化
│   ├── bootstrap.py               # 路由注册、蓝图注册、启动任务
│   ├── models.py                  # ORM 数据模型
│   ├── init_db.py                 # 自动建表和轻量迁移
│   ├── auth.py                    # 登录态、Token、账本权限辅助
│   ├── core.py                    # 日志、错误处理、健康检查、汇率服务
│   ├── routes_base.py             # Web 页面、登录注册、管理员页面
│   ├── routes_transactions.py     # 交易、报销、核销、管理员用户操作
│   ├── routes_finance.py          # 账户、预算、借贷、周期账单、报表
│   ├── routes_ledgers.py          # 账本、成员、邀请码
│   └── routes_miniapp.py          # 小程序认证、概览、头像/附件上传
├── blueprints/
│   ├── import_export.py           # 导入导出模块
│   └── smart_bookkeeping.py       # 文本智能记账和 AI 财务分析
├── templates/                     # Web 页面模板
├── static/                        # 静态资源、头像、上传文件
├── data/                          # 运行数据、导入文件、导出文件
├── logs/                          # 运行日志
└── miniprogram/                   # uni-app 小程序端
```

## 快速开始

### 1. 准备环境

- Python 3.10 或更高版本
- MySQL 5.7 / 8.x
- Node.js 18 或更高版本，小程序端开发需要
- HBuilderX、微信开发者工具或 uni-app CLI

### 2. 安装后端依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 创建数据库

请先创建 MySQL 数据库，并确认 `config.py` 中的 `SQLALCHEMY_DATABASE_URI` 指向正确的数据库实例。

```bash
mysql -u root -p -e "CREATE DATABASE db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

应用启动时会执行 `db.create_all()`，并在 `cash_app/init_db.py` 中补齐必要字段、创建默认分类、默认账号和轻量迁移。历史“个人账本”会迁移到个人模式，即个人数据使用 `ledger_id = NULL`。

### 4. 启动后端

```bash
python run.py
```

默认访问地址：

| 入口 | 地址 |
| --- | --- |
| Web 首页 | `http://127.0.0.1:8080/` |
| 管理后台 | `http://127.0.0.1:8080/admin` |
| 健康检查 | `http://127.0.0.1:8080/health` |
| API 信息 | `http://127.0.0.1:8080/api/info` |

### 5. 默认账号

首次初始化会创建以下开发账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123` |

生产环境部署前必须修改默认账号密码和所有敏感配置。

## 小程序端

小程序代码位于 `miniprogram/`。后端地址在 `miniprogram/config/index.js` 中配置。

### 安装依赖

```bash
cd miniprogram
npm install
```

### 微信小程序构建

```bash
npm run build:mp-weixin
```

构建产物输出到 `miniprogram/dist/mp-weixin/`。微信开发者工具导入 `miniprogram/` 目录即可，项目配置中的 `miniprogramRoot` 指向构建产物目录。

### 开发监听

```bash
npm run dev:mp-weixin
```

真机调试时不要使用 `127.0.0.1`。请将小程序 `baseUrl` 改为电脑局域网 IP，例如：

```js
development: {
  baseUrl: 'http://192.168.1.10:8080',
}
```

手机和电脑需要处于同一网络，并确保防火墙允许访问后端端口。

## 核心功能

### 用户与认证

- Web 表单登录、注册、退出、找回密码、重置密码、修改密码。
- 小程序 Token 登录、注册、登出和登录过期自动跳转。
- 用户资料维护，包括头像、邮箱、手机号、昵称和密码。
- 管理员支持平台数据概览、用户管理、交易查看、重置用户密码、删除普通用户。

### 账本与成员协作

- 个人模式使用 `ledger_id = NULL` 保存个人数据，不再额外创建“个人账本”。
- 共享账本支持创建、编辑、删除、切换和成员管理。
- 账本角色包括：

| 角色 | 权限说明 |
| --- | --- |
| `viewer` | 可查看账本数据 |
| `editor` | 可新增和编辑账本业务数据 |
| `manager` | 可管理账本、成员和邀请码 |
| `owner` | 账本所有者，具有最高管理权限 |

- 邀请码可设置有效期和使用次数。
- 用户通过邀请码加入共享账本后默认成为 `editor`。
- 个人模式不支持分享加入、邀请码和成员管理。

### 交易流水

- 支持收入、支出、转账、预付款等业务类型。
- 支持分类、日期、时间、账户、备注、币种、原始金额、汇率、附件和地理位置。
- 支持 AA 分摊、付款人、成员分摊明细和统计开关。
- 支持日期、分类、类型、账户、金额区间、关键词等筛选。
- 创建、更新、删除交易会联动账户余额并记录资金变动日志。

### 财务管理

- 账户管理：创建、修改、删除账户，维护现金、银行卡、信用卡和其他账户。
- 预算管理：按月份设置总预算和分类预算，统计预算使用情况。
- 借贷管理：记录借入、借出、还款、收款、到期日和结清状态。
- 报销管理：标记报销状态，支持部分报销、全部报销和核销交易。
- 周期账单：支持每日、每周、每月、每年规则，启动时自动生成到期账单。
- 报表分析：提供日、周、月、年和高级报表，支持图表展示与下载。

### 数据导入导出

- 导入支持 `.csv`、`.xlsx`、`.xls`。
- 上传后会生成预览数据，并支持字段映射和确认导入。
- 导出支持 CSV / XLSX，大数据量会创建异步导出任务。
- 可查看导出任务状态、下载导出文件、删除导出任务。
- 配置 SMTP 后可将导出文件发送到指定邮箱。

### 智能记账与 AI 分析

- 文本智能记账：`/api/smart/parse` 将自然语言文本解析为一条或多条候选账单。
- 确认入账：`/api/smart/confirm` 将解析结果写入交易流水。
- 小程序智能记账页面支持粘贴文本、解析结果逐条确认或全部入账。
- 当前智能记账不使用 OCR，不提供图片识别入口。
- AI 财务分析：`/api/smart/deepseek-analysis` 可基于指定周期账单生成财务分析。
- AI 分析历史支持查询、详情查看和删除。

## 常用 API

大部分业务 API 需要登录。Web 端使用 Flask Session，小程序端使用 `Authorization: Bearer <token>`。

| 模块 | 接口 |
| --- | --- |
| 健康检查 | `GET /health` |
| API 信息 | `GET /api/info` |
| 认证 | `POST /api/auth/login`, `POST /api/auth/register`, `POST /api/auth/logout` |
| 密码 | `POST /api/auth/forgot-password`, `POST /api/auth/reset-password`, `POST /api/auth/change-password` |
| 用户资料 | `GET /api/user/profile`, `PUT /api/user/profile`, `POST /api/user/change-password` |
| 小程序 | `POST /api/miniapp/login`, `POST /api/miniapp/register`, `GET /api/miniapp/dashboard`, `POST /api/miniapp/upload` |
| 账本 | `GET /api/ledgers`, `POST /api/ledgers`, `GET/PUT/DELETE /api/ledgers/<id>` |
| 账本切换 | `POST /api/ledgers/<id>/switch`, `POST /api/ledgers/personal` |
| 账本成员 | `GET/POST /api/ledgers/<id>/members`, `PUT/DELETE /api/ledgers/<id>/members/<user_id>` |
| 邀请码 | `GET/POST /api/ledgers/<id>/invite-codes`, `DELETE /api/ledgers/<id>/invite-codes/<code_id>` |
| 加入账本 | `POST /api/ledgers/validate-code`, `POST /api/ledgers/join` |
| 交易 | `GET/POST /api/transactions`, `GET/PUT/DELETE /api/transactions/<id>` |
| 报销 | `GET /api/reimbursements`, `PUT /api/transactions/<id>/reimbursement`, `POST /api/transactions/<id>/write-off` |
| 账户 | `GET/POST /api/accounts`, `PUT/DELETE /api/accounts/<id>` |
| 分类 | `GET /api/categories` |
| 预算 | `GET /api/budgets/current`, `GET /api/budgets/list`, `POST /api/budgets`, `DELETE /api/budgets/<id>` |
| 借贷 | `GET/POST /api/loans`, `PUT/DELETE /api/loans/<id>`, `POST /api/loans/<id>/repay`, `GET /api/loans/summary` |
| 周期账单 | `GET/POST /api/recurring-rules`, `PUT/DELETE /api/recurring-rules/<id>`, `POST /api/recurring-rules/generate` |
| 报表 | `GET /api/reports/<period>`, `GET /api/reports/advanced`, `GET /api/reports/download` |
| 导入 | `POST /api/import/upload`, `POST /api/import/confirm` |
| 导出 | `POST /api/export/create`, `GET /api/export/status/<task_id>`, `GET /api/export/download/<task_id>`, `GET /api/export/list` |
| 智能记账 | `POST /api/smart/parse`, `POST /api/smart/confirm` |
| AI 分析 | `GET /api/smart/deepseek-analysis`, `GET/DELETE /api/smart/ai-analysis`, `GET/DELETE /api/smart/ai-analysis/<id>` |
| 资金日志 | `GET /api/money-change-logs` |
| 管理员 | `POST /api/admin/users/<user_id>/reset-password`, `DELETE /api/admin/users/<user_id>` |

## 数据模型概览

| 表 | 说明 |
| --- | --- |
| `users` | 用户、管理员标记、头像和个人资料 |
| `categories` | 收入和支出分类 |
| `accounts` | 用户或账本下的账户余额 |
| `transactions` | 核心交易流水 |
| `transaction_splits` | AA 分摊明细 |
| `budgets` | 月度预算 |
| `budget_category_items` | 分类预算 |
| `ledgers` | 共享账本 |
| `ledger_members` | 账本成员和角色 |
| `invite_codes` | 账本邀请码 |
| `loans` | 借入和借出记录 |
| `recurring_rules` | 周期账单规则 |
| `ai_analysis` | AI 财务分析历史 |
| `export_tasks` | 导出任务 |
| `file_uploads` | 导入文件记录 |
| `money_change_logs` | 资金变动日志 |

## 配置说明

主要配置集中在 `config.py`。以下配置可通过环境变量或配置文件调整：

| 配置 | 说明 |
| --- | --- |
| `APP_NAME` | 应用名称 |
| `SECRET_KEY` | Flask Session 密钥，生产环境必须替换 |
| `HOST` / `PORT` | 后端监听地址和端口 |
| `DATA_DIR` | 运行数据目录 |
| `LOG_DIR` / `LOG_LEVEL` | 日志目录和日志级别 |
| `MAX_TRANSACTIONS_DISPLAY` | 交易列表最大展示数量 |
| `BACKUP_ENABLED` / `BACKUP_DIR` | 本地备份开关和目录 |
| `UPLOAD_DIR` / `MAX_UPLOAD_SIZE_MB` | 导入上传目录和大小限制 |
| `EXPORT_DIR` / `EXPORT_ASYNC_THRESHOLD` | 导出目录和异步导出阈值 |
| `SQLALCHEMY_DATABASE_URI` | MySQL 连接字符串 |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_USE_TLS` | 邮件服务配置 |
| `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | 邮件账号、授权码和发件人 |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` | AI 分析服务配置 |
| `DEEPSEEK_TIMEOUT` | AI 请求超时时间 |

注意：仓库中的 `config.py` 带有开发环境默认值。生产环境不要直接使用硬编码密钥、数据库密码、邮箱授权码或 API Key，建议通过环境变量、私有配置文件或密钥管理服务注入。

## 启动机制

应用启动时会依次执行：

1. 创建 Flask 应用并初始化 SQLAlchemy。
2. 导入路由模块并注册蓝图。
3. 执行 `initialize_db()`，创建表结构、补齐字段、写入默认分类和默认账号。
4. 将历史“个人账本”迁移到个人模式。
5. 扫描已到期的周期账单规则，并自动生成应入账交易。
6. 启动 Flask Web 服务。

## 开发注意事项

- 项目当前未引入 Alembic，数据库轻量迁移写在 `cash_app/init_db.py`。修改模型后需要同步补充迁移逻辑。
- 小程序请求地址由 `miniprogram/config/index.js` 控制，后端端口或域名变化时需要同步修改。
- Web 报表和后台图表依赖 ECharts / Bootstrap 等前端资源，离线部署时需要检查资源加载方式。
- `data/`、`logs/`、上传文件和导出文件属于运行时数据，不应直接提交生产数据。
- 当前 README 只描述文本智能记账；图片 OCR 入口和 OCR 解析代码已移除。

## 生产部署建议

- 修改 `SECRET_KEY`、默认账号密码、数据库账号密码、SMTP 授权码和 DeepSeek API Key。
- 为数据库创建独立低权限账号，并开启定期备份。
- 使用 Gunicorn、uWSGI 或其他 WSGI 服务托管 Flask，不建议生产环境直接运行 `python run.py`。
- 使用 Nginx 或其他反向代理统一处理 HTTPS、静态资源和上传大小限制。
- 对 `static/uploads/`、`data/uploads/`、`data/exports/` 做权限隔离和定期清理。
- 配置日志轮转、异常监控和数据库备份策略。
- 小程序正式发布时，将 `production.baseUrl` 设置为可访问的 HTTPS 域名，并在微信公众平台配置合法域名。

## 故障排查

| 问题 | 处理方式 |
| --- | --- |
| 端口被占用 | 修改 `PORT` 环境变量，或释放默认端口 |
| 数据库连接失败 | 检查 MySQL 服务、账号密码、数据库名和 `SQLALCHEMY_DATABASE_URI` |
| 表字段缺失 | 重启应用，让 `initialize_db()` 执行轻量迁移 |
| 小程序请求失败 | 检查 `baseUrl`、后端是否启动、真机是否能访问电脑局域网 IP |
| 登录过期 | 小程序端会清理 Token 并跳转登录页，请重新登录 |
| 智能解析失败 | 检查输入文本格式、分类和账户数据是否存在 |
| AI 分析失败 | 检查 DeepSeek 配置、模型名、网络和接口额度 |
| 导出邮件失败 | 检查 SMTP 地址、端口、TLS、邮箱账号和授权码 |
| 邀请码加入后权限不对 | 新加入用户应为 `editor`，旧成员角色需在成员管理中手动调整 |

## 许可证

当前仓库未声明开源许可证。如需对外发布，请先补充 LICENSE 文件并明确使用范围。
