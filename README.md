# 线上记账管理系统

基于 Flask 的在线记账项目，支持多用户、多账本、预算管理、借贷管理、报销核销、数据导入导出、智能记账和 uni-app 小程序端。

## 技术栈

- 后端：Flask 3.x、Flask-SQLAlchemy、Flask-CORS
- 数据库：MySQL + PyMySQL
- 前端：Jinja2、Bootstrap 5、原生 JavaScript、ECharts
- 数据处理：openpyxl、chardet、python-dateutil
- AI 辅助：DeepSeek API
- 小程序端：uni-app

## 项目结构

```text
.
├── app.py
├── run.py
├── config.py
├── db_test.sql
├── requirements.txt
├── cash_app/
├── blueprints/
├── templates/
├── static/
├── data/
└── miniprogram/
```

## 主要功能

- 用户注册、登录、个人资料和修改密码
- 多账本管理、成员邀请与切换
- 收支记账、分类统计、报表分析
- 预算管理、超支预警
- 借入/借出、还款记录
- 报销标记与核销
- 周期性账单自动生成
- Excel/CSV 导入导出
- 智能记账与 DeepSeek 分析
- 管理员后台
- uni-app 小程序端

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置数据库

默认数据库配置在 [config.py](./config.py) 中：

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/db_test'
```

请先创建数据库：

```bash
mysql -u root -p -e "CREATE DATABASE db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

可选：导入参考结构脚本

```bash
mysql -u root -p db_test < db_test.sql
```

### 3. 启动项目

推荐使用：

```bash
python run.py
```

默认监听 `http://127.0.0.1:8080`。

也可以直接运行：

```bash
python app.py
```

## 默认账号

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123` |

## 管理后台

管理员登录后可进入后台，支持：

- 平台统计
- 用户统计
- 数据分析看板
- 全平台交易记录
- 用户管理

说明：管理员自己的记账数据不计入平台统计，后台只展示普通用户数据。

## 小程序端

`miniprogram/` 下是 uni-app 小程序端，对接后端 API：

- 登录/注册：`/api/miniapp/login`、`/api/miniapp/register`
- 仪表盘：`/api/miniapp/dashboard`
- 头像上传：`/api/miniapp/upload`

如果后端地址变化，请同步修改：

- `miniprogram/services/api.js`
- `miniprogram/pages/profile/index.vue`
- `cash_app/routes_miniapp.py`

## 环境变量

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `APP_NAME` | 线上记账管理系统 | 应用名称 |
| `SECRET_KEY` | dev-secret-key-change-in-production | 会话密钥 |
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8080` | 监听端口 |
| `DATA_DIR` | `data` | 数据目录 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `MAX_TRANSACTIONS_DISPLAY` | `10000` | 最大展示交易数 |
| `BACKUP_ENABLED` | `true` | 是否启用自动备份 |
| `DEEPSEEK_API_KEY` | - | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek 接口地址 |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek 模型 |
| `SMTP_SERVER` | `smtp.qq.com` | SMTP 服务器 |

## 数据库初始化

项目启动时会自动执行：

1. `db.create_all()` 创建缺失表
2. 数据迁移补字段
3. 初始化默认分类
4. 初始化默认用户
5. 为用户创建默认账本和默认账户
6. 启动时补生成到期的周期账单

## 备注

- `db_test.sql` 主要用于结构参考，不是唯一启动方式
- 当前代码中部分头像和本地接口地址默认指向 `127.0.0.1:8080`
- 生产环境部署前请务必修改 `SECRET_KEY`、数据库密码和 DeepSeek 配置
