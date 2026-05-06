# 线上记账系统

这是一个基于 Flask 的轻量级在线记账管理系统，提供完整的用户认证、账目管理、数据导入导出、智能记账辅助和报表统计功能。系统采用模块化架构设计，支持多用户管理、数据安全和便捷的财务分析。

## 项目架构

### 技术栈
- **后端框架**: Flask 3.0.0
- **Web 服务器**: Gunicorn 21.2.0 (生产环境)
- **数据库**: MySQL (通过 Flask-SQLAlchemy)
- **前端**: Jinja2 模板 + 原生 HTML5/CSS3/JavaScript
- **数据处理**: openpyxl 3.1.2, xlrd 2.0.1, chardet 5.2.0
- **HTTP 客户端**: requests 2.31.0
- **环境管理**: python-dotenv 1.0.0
- **CORS 支持**: flask-cors 4.0.0

### 项目结构
```
线上记账系统/
├── app.py              # Flask 应用核心
├── run.py              # 开发环境启动脚本
├── config.py           # 配置管理
├── requirements.txt    # Python 依赖
├── blueprints/         # 功能模块
│   ├── import_export.py    # 数据导入导出模块
│   └── smart_bookkeeping.py # 智能记账模块
├── templates/          # 前端页面模板
│   ├── index.html         # 主页
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   ├── admin.html         # 管理员页面
│   ├── user_profile.html   # 用户资料
│   ├── reports.html       # 报表页面
│   ├── data_tools.html    # 数据工具
│   ├── change_password.html # 修改密码
│   ├── forgot_password.html # 忘记密码
│   └── reset_password.html  # 重置密码
├── static/             # 静态资源
│   ├── css/              # 样式文件
│   │   └── style.css
│   ├── js/               # JavaScript 文件
│   │   ├── app.js
│   │   └── data_tools.js
│   └── avatars/          # 用户头像
│       ├── default_avatar.svg
│       └── 53c6c55497424c16a3b37b8b709e835c.jpg
├── data/               # 数据存储目录
│   ├── uploads/          # 文件上传目录
│   ├── exports/          # 导出文件目录
│   └── backups/          # 备份目录
├── logs/                # 日志目录
└── db_test.sql          # 数据库初始化脚本
```

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd 线上记账系统
```

### 2. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库设置
```bash
# 创建数据库
mysql -u 用户名 -p -e "CREATE DATABASE db_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入初始数据
mysql -u 用户名 -p db_test < db_test.sql
```

### 4. 配置文件
编辑 `config.py`：
```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://用户名:密码@localhost:3306/db_test'

# 文件存储路径
UPLOAD_FOLDER = 'data/uploads'
EXPORT_FOLDER = 'data/exports'
BACKUP_FOLDER = 'data/backups'

# 邮件配置（可选）
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@example.com'
MAIL_PASSWORD = 'your-password'
```

### 5. 运行应用
```bash
# 开发模式
python run.py

# 或生产模式
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### 6. 访问应用
- 前端主页: `http://localhost:8080`
- 管理员面板: `http://localhost:8080/admin`
- 用户登录: `http://localhost:8080/login`

### 7. 创建管理员账户
如果需要创建自定义管理员账户，请按照以下步骤：

#### 方法1：使用Python脚本生成密码哈希

1. 创建 `generate_admin_hash.py` 文件：
```python
from werkzeug.security import generate_password_hash

# 设置您的管理员密码
admin_password = 'your_password_here'  # 替换为您想要的密码

# 生成密码哈希
password_hash = generate_password_hash(admin_password)
print(f"管理员密码哈希: {password_hash}")
print(f"请使用以下SQL语句创建管理员账户:")
print(f"INSERT INTO users (username, password_hash, is_admin) VALUES ('admin', '{password_hash}', 1);")
```

2. 运行脚本：
```bash
python generate_admin_hash.py
```

3. 在MySQL中执行生成的SQL语句：
```sql
INSERT INTO users (username, password_hash, is_admin) VALUES ('admin', '生成的哈希值', 1);
```

#### 方法2：直接在MySQL中创建（不推荐用于生产环境）

```sql
INSERT INTO users (username, password_hash, is_admin) VALUES ('admin', 'your_hash_here', 1);
```

### 8. 默认账户
- 管理员: admin / admin123
- 普通用户: user / user123

### 9. 首次使用
1. 登录系统
2. 添加账目记录
3. 尝试数据导入导出功能
4. 查看报表统计

## 环境配置

### 环境变量
可以通过环境变量自定义配置：
```bash
export FLASK_ENV=production
export HOST=0.0.0.0
export PORT=8080
export DATABASE_URL='mysql+pymysql://用户名:密码@localhost:3306/数据库名'
```

### 配置文件
主要配置文件 `config.py` 包含：
- 数据库连接配置
- 文件存储路径
- 邮件服务配置
- 业务参数设置
- 安全设置

## 注意事项

- 确保 MySQL 服务正常运行
- 检查文件权限（特别是 data 目录）
- 生产环境建议配置 HTTPS
- 定期备份数据库和重要文件
- 监控系统资源使用情况
- 定期更新依赖库以获取安全补丁

## 运行系统

### 开发环境运行
```bash
# 启用开发模式（热重载）
python run.py
```

- **默认端口**: 8080
- **访问地址**:
  - 前端主页: `http://localhost:8080`
  - 后台管理: `http://localhost:8080/admin`
  - 健康检查: `http://localhost:8080/health`
  - 用户登录: `http://localhost:8080/login`
  - 用户注册: `http://localhost:8080/register`

### 生产环境运行
使用 Gunicorn 部署（推荐配置）：
```bash
# 基础配置
gunicorn -w 4 -b 0.0.0.0:8080 app:app

# 高级配置（生产环境）
gunicorn -w 4 -k gevent -b 0.0.0.0:8080 --access-logfile - --error-logfile - app:app
```

### Docker 部署（可选）
```bash
# 构建镜像
docker build -t cash-system .

# 运行容器
docker run -p 8080:8080 cash-system
```

## 环境配置

### 环境变量
可以通过环境变量自定义配置：
```bash
export FLASK_ENV=production
export HOST=0.0.0.0
export PORT=8080
```

### 配置文件
主要配置文件 `config.py` 包含：
- 数据库连接配置
- 文件存储路径
- 邮件服务配置
- 业务参数设置

## 功能特性

### 核心功能
- 📊 **账目管理**: 支持收入、支出记录，分类管理，金额统计
- 📤 **数据导入导出**: Excel/CSV格式数据导入，支持多种导出格式
- 🤖 **智能记账**: 自动分类，智能建议，重复账目识别
- 🔐 **用户系统**: 完整的用户注册、登录、密码重置功能
- 📋 **后台管理**: 管理员面板，用户管理，系统配置
- 📈 **数据报表**: 可视化统计图表，月度/年度财务分析
- 📱 **响应式设计**: 适配桌面和移动设备
- 🔒 **数据安全**: 用户密码加密存储，数据备份机制

### 特色功能
- **热重载开发**: 开发模式下自动重启服务，提升开发效率
- **智能目录管理**: 启动时自动创建必要的存储目录
- **邮件通知系统**: 支持SMTP邮件发送，密码重置通知
- **数据备份**: 定期自动备份，防止数据丢失
- **异步导出**: 大数据量导出优化，避免超时
- **健康检查**: 系统状态监控，服务可用性检查
- **跨域支持**: 支持前后端分离部署
- **环境变量配置**: 灵活的配置管理，支持多环境部署

## 开发指南

### 开发环境设置
```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 启用开发模式（热重载）
python run.py
```

### 代码结构
- `app.py`: 主应用文件，包含核心路由和初始化
- `blueprints/`: 模块化功能实现
  - `import_export.py`: 数据导入导出功能
  - `smart_bookkeeping.py`: 智能记账功能
- `templates/`: 前端页面模板
- `static/`: 静态资源文件
- `config.py`: 配置管理

### 调试和测试
- **开发模式**: 自动热重载，详细错误信息
- **调试工具**: 使用 Flask 调试器进行问题排查
- **日志**: 查看 logs/app.log 获取详细运行信息
- **测试**: 编写单元测试和集成测试

### 代码规范
- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写文档字符串
- 添加必要的注释

### 常见问题排查
- **数据库连接失败**: 检查 `config.py` 中的数据库配置
- **文件权限问题**: 确保 `data/` 目录可写
- **导入导出错误**: 检查文件格式和权限
- **前端样式问题**: 清除浏览器缓存，检查 CSS 文件

### 贡献指南
欢迎提交 Issue 和 Pull Request！请确保：
1. 代码符合项目规范和代码风格
2. 添加必要的测试用例
3. 更新相关文档
4. 遵循现有的代码结构和设计模式
5. 提交前运行测试确保功能正常

## 部署说明

### 生产环境部署
1. **配置环境变量**
   ```bash
   export FLASK_ENV=production
   export HOST=0.0.0.0
   export PORT=8080
   export DATABASE_URL='mysql+pymysql://用户名:密码@localhost:3306/数据库名'
   ```

2. **使用 Gunicorn 部署**
   ```bash
   gunicorn -w 4 -k gevent -b 0.0.0.0:8080 --access-logfile - --error-logfile - app:app
   ```

3. **配置 Nginx 反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **设置 HTTPS 证书**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **配置日志轮转**
   ```bash
   # /etc/logrotate.d/cash-system
   /var/log/cash/*.log {
       daily
       rotate 7
       compress
       missingok
       notifempty
   }
   ```

### 数据迁移
- **初始化数据库**: 运行 `db_test.sql` 创建表结构
- **数据迁移**: 使用数据库迁移工具迁移现有数据
- **定期备份**: 配置自动备份脚本，定期备份数据库和重要文件
- **监控**: 设置健康检查和监控告警

### Docker 部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
```

## 注意事项

- 确保 MySQL 服务正常运行
- 检查文件权限（特别是 data 目录）
- 生产环境建议配置 HTTPS
- 定期备份数据库和重要文件

## 贡献指南

欢迎提交 Issue 和 Pull Request！请确保：
1. 代码符合项目规范和代码风格
2. 添加必要的测试用例
3. 更新相关文档
4. 遵循现有的代码结构和设计模式
5. 提交前运行测试确保功能正常

### 贡献流程
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 编写测试
5. 提交 Pull Request

### 联系方式
- 问题反馈: 通过 GitHub Issues
- 功能建议: 通过 GitHub Discussions
- 贡献代码: 通过 Pull Request

## 许可证

本项目采用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。

## 致谢

感谢所有为这个项目做出贡献的开发者和用户！

## 支持

如需帮助或有问题，请：
- 查看 [文档](README.md)
- 提交 [Issue](https://github.com/your-repo/issues)
- 联系项目维护者

## 更新日志

### v1.0.0
- 初始版本发布
- 基础记账功能
- 用户认证系统
- 数据导入导出
- 报表统计

### v1.1.0
- 智能记账功能
- 改进的用户界面
- 性能优化
- 安全增强

## 未来计划

- 移动端应用支持
- 多语言国际化
- 高级数据分析
- API 接口
- 云服务集成

## 联系我们

如有问题或建议，请通过以下方式联系我们：
- 邮箱: support@cash-system.com
- 网站: https://cash-system.example.com
- GitHub: https://github.com/your-repo
