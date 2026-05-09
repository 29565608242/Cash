# 小程序端开发指南 — 将记账系统扩展到微信/支付宝小程序

> **目标**：基于现有 Flask 后端，构建微信小程序 + 支付宝小程序双端应用，功能与网页版保持一致，针对移动端重新设计 UI 排版。

---

## 一、项目现状分析

### 1.1 后端技术栈
| 模块 | 技术 |
|------|------|
| Web 框架 | Flask 3.0 |
| ORM | SQLAlchemy + PyMySQL |
| 数据库 | MySQL |
| 认证 | Session + Cookie |
| 前端 | Jinja2 + 原生 JS + ECharts |
| 智能记账 | DeepSeek API |
| 导入导出 | openpyxl, csv |

### 1.2 后端 API 清单（全部可用）

后端已提供完整的 RESTful API，小程序直接复用，无需重写后端业务逻辑：

| 模块 | API 端点 | 方法 | 说明 |
|------|----------|------|------|
| **认证** | `/api/auth/login` (需新增) | POST | 小程序登录（见下文 3.1） |
| | `/api/auth/logout` | POST | 登出 |
| | `/api/user/profile` | GET/PUT | 用户信息 |
| | `/api/user/change-password` | POST | 修改密码 |
| **交易** | `/api/transactions` | GET | 交易列表（分页/筛选） |
| | `/api/transactions` | POST | 创建交易 |
| | `/api/transactions/{id}` | PUT | 更新交易 |
| | `/api/transactions/{id}` | DELETE | 删除交易 |
| | `/api/categories` | GET | 分类列表 |
| **账户** | `/api/accounts` | GET | 账户列表 |
| | `/api/accounts` | POST | 创建账户 |
| | `/api/accounts/{id}` | PUT | 更新账户 |
| | `/api/accounts/{id}` | DELETE | 删除账户 |
| **账本** | `/api/ledgers` | GET/POST | 账本列表/创建 |
| | `/api/ledgers/{id}` | GET/PUT/DELETE | 账本详情/更新/删除 |
| | `/api/ledgers/{id}/switch` | POST | 切换账本 |
| | `/api/ledgers/{id}/members` | GET/POST | 成员管理 |
| | `/api/ledgers/{id}/invite-codes` | GET/POST | 邀请码 |
| | `/api/ledgers/join` | POST | 加入账本 |
| | `/api/ledgers/validate-code` | POST | 校验邀请码 |
| **预算** | `/api/budgets/current` | GET | 当月预算 |
| | `/api/budgets` | POST | 创建/更新预算 |
| | `/api/budgets/{id}` | DELETE | 删除预算 |
| **借贷** | `/api/loans` | GET/POST | 借贷列表/创建 |
| | `/api/loans/{id}` | PUT/DELETE | 更新/删除 |
| | `/api/loans/{id}/repay` | POST | 还款/收款 |
| | `/api/loans/summary` | GET | 借贷汇总 |
| **报销** | `/api/reimbursements` | GET | 报销列表 |
| | `/api/transactions/{id}/reimbursement` | PUT | 更新报销状态 |
| | `/api/transactions/{id}/write-off` | POST | 核销报销 |
| **周期账单** | `/api/recurring-rules` | GET/POST | 规则列表/创建 |
| | `/api/recurring-rules/{id}` | PUT/DELETE | 更新/删除 |
| | `/api/recurring-rules/{id}/toggle` | POST | 启用/停用 |
| | `/api/recurring-rules/generate` | POST | 手动生成 |
| **报表** | `/api/reports/advanced` | GET | 高级报表 |
| | `/api/reports/{period}` | GET | 周期报表 |
| **智能记账** | `/api/smart/parse` | POST | 自然语言解析 |
| | `/api/smart/confirm` | POST | 确认智能记账 |
| | `/api/smart/deepseek-analysis` | GET | AI 分析 |
| **导入导出** | `/api/import/upload` | POST | 上传文件 |
| | `/api/import/confirm` | POST | 确认导入 |
| | `/api/export/create` | POST | 创建导出任务 |
| | `/api/export/download/{id}` | GET | 下载导出文件 |
| **资金变动** | `/api/money-change-logs` | GET | 资金变动记录 |

### 1.3 网页版功能模块对照

| 功能模块 | 网页版 | 小程序 | 备注 |
|----------|--------|--------|------|
| 登录/注册 | ✅ | ✅ | 小程序使用 code 登录 + token |
| 首页看板 | ✅ | ✅ | 重新设计为移动卡片布局 |
| 交易流水 | ✅ | ✅ | 列表 + 筛选 + 搜索 |
| 记一笔 | ✅ | ✅ | 收入/支出表单 |
| 账户管理 | ✅ | ✅ | 多账户 |
| 分类管理 | ✅ | ✅ | 内置默认分类 |
| 多账本 | ✅ | ✅ | 共享账本 |
| 预算管理 | ✅ | ✅ | 月度预算 + 分类预算 |
| 借贷管理 | ✅ | ✅ | 借入/借出 + 还款 |
| 报销管理 | ✅ | ✅ | 标记报销 + 核销 |
| 周期账单 | ✅ | ✅ | 自动生成定期交易 |
| 报表统计 | ✅ | ✅ | 图表简化适配移动端 |
| AI 分析 | ✅ | ✅ | DeepSeek |
| 智能记账 | ✅ | ✅ | NLP 解析文本 |
| 导入导出 | ✅ | ❌ | 小程序文件 API 有限 |
| 管理后台 | ✅ | ❌ | 管理员功能保留在网页 |
| 多币种 | ✅ | ✅ | 汇率转换 |

---

## 二、架构设计

### 2.1 总体架构

```
┌─────────────────────────────────┐
│  微信小程序 / 支付宝小程序       │
│  ┌───────────┐ ┌──────────────┐ │
│  │ 页面层     │ │ 组件层        │ │
│  │ (pages/)  │ │ (components/)│ │
│  └───────────┘ └──────────────┘ │
│  ┌────────────────────────────┐ │
│  │ 服务层 (services/)         │ │
│  │ API 调用 / 缓存 / 工具函数 │ │
│  └────────────────────────────┘ │
│  ┌────────────────────────────┐ │
│  │ 状态管理 (store/)          │ │
│  └────────────────────────────┘ │
└──────────┬──────────────────────┘
           │ HTTPS + JSON
           ▼
┌─────────────────────────────────┐
│  Flask 后端 (复用现有代码)      │
│  新增: token 认证适配层          │
│  新增: 小程序登录接口            │
│  不变: 所有业务 API              │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  MySQL 数据库 (不变)            │
└─────────────────────────────────┘
```

### 2.2 目录结构（微信小程序）

```
miniprogram/
├── app.json                    # 小程序全局配置
├── app.wxss                    # 全局样式
├── app.js                      # 全局入口
├── project.config.json         # 项目配置
├── sitemap.json
│
├── assets/                     # 静态资源
│   ├── icons/                  # 图标（收入/支出/分类等）
│   ├── images/                 # 图片（背景、占位图）
│   └── fonts/                  # 字体
│
├── components/                 # 公共组件
│   ├── amount-input/           # 金额输入组件
│   ├── category-picker/        # 分类选择器
│   ├── date-picker/            # 日期选择器
│   ├── account-picker/         # 账户选择器
│   ├── ledger-switcher/        # 账本切换器
│   ├── stat-card/              # 统计卡片
│   ├── transaction-item/       # 交易列表项
│   ├── empty-state/            # 空状态
│   ├── loading/                # 加载动画
│   ├── nav-bar/                # 自定义导航栏
│   ├── tab-bar/                # 底部标签栏
│   └── modal/                  # 弹窗组件
│
├── pages/                      # 页面
│   ├── login/                  # 登录页
│   ├── register/               # 注册页
│   ├── index/                  # 首页看板
│   ├── transactions/           # 交易列表
│   ├── transaction-add/        # 记一笔
│   ├── transaction-edit/       # 编辑交易
│   ├── transaction-detail/     # 交易详情
│   ├── accounts/               # 账户管理
│   ├── ledgers/                # 账本管理
│   ├── ledger-members/         # 成员管理
│   ├── budget/                 # 预算管理
│   ├── loans/                  # 借贷管理
│   ├── loan-add/               # 新增借贷
│   ├── reimbursement/          # 报销管理
│   ├── recurring/              # 周期账单
│   ├── recurring-add/          # 新增周期规则
│   ├── reports/                # 报表统计
│   ├── smart-bookkeeping/      # 智能记账
│   ├── ai-analysis/            # AI 分析
│   ├── profile/                # 个人中心
│   ├── change-password/        # 修改密码
│   └── about/                  # 关于
│
├── services/                   # 服务层
│   ├── api.js                  # 核心 API 封装
│   ├── auth.js                 # 认证服务
│   ├── cache.js                # 缓存管理
│   └── utils.js                # 工具函数
│
├── store/                      # 状态管理
│   └── index.js                # 全局状态
│
└── styles/                     # 样式
    ├── variables.wxss          # 设计变量
    ├── reset.wxss              # 重置样式
    └── components.wxss         # 组件通用样式
```

### 2.3 支付宝小程序适配

支付宝小程序结构与微信类似，差异仅在：

| 差异点 | 微信 | 支付宝 |
|--------|------|--------|
| 文件后缀 | .wxml/.wxss/.js/.json | .axml/.acss/.js/.json |
| 登录 API | wx.login | my.getAuthCode |
| 网络请求 | wx.request | my.request |
| 存储 | wx.setStorageSync | my.setStorageSync |
| API 命名 | wx.* | my.* |

**推荐方案**：使用 **uni-app**（Vue.js 跨端框架）一套代码编译到两端，大幅降低维护成本。本指南后续以 uni-app 为主进行说明。

---

## 三、后端适配改造

小程序需要后端新增/修改以下接口：

### 3.1 小程序登录接口

**文件**：`cash_app/routes_miniapp.py`（新增）

```python
# cash_app/routes_miniapp.py
import hashlib, time, json
from flask import Blueprint, jsonify, request, session
from .app_state import app, db
from .models import User, Ledger, LedgerMember, Account

miniapp_bp = Blueprint('miniapp', __name__, url_prefix='/api/miniapp')

# Token 存储（生产环境应使用 Redis）
_tokens = {}  # {token: {user_id, expires_at}}

def generate_token(user_id):
    """生成登录 Token"""
    raw = f"{user_id}:{time.time()}:{app.config['SECRET_KEY']}"
    token = hashlib.sha256(raw.encode()).hexdigest()
    _tokens[token] = {
        'user_id': user_id,
        'expires_at': time.time() + 86400 * 7  # 7天有效期
    }
    return token

def token_required(f):
    """小程序 Token 认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else auth_header
        info = _tokens.get(token)
        if not info or info['expires_at'] < time.time():
            if info:
                del _tokens[token]
            return jsonify({'success': False, 'message': '登录已过期，请重新登录'}), 401
        request.current_user = User.query.get(info['user_id'])
        if not request.current_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/miniapp/login', methods=['POST'])
def miniapp_login():
    """小程序登录：用户名密码 → token"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()
    token = generate_token(user.id)
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'email': user.email
        }
    })

@app.route('/api/miniapp/register', methods=['POST'])
def miniapp_register():
    """小程序注册"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码必填'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': '密码至少6位'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已被注册'}), 400
    user = User(username=username, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    # 创建默认账本和账户
    ledger = Ledger(name=f"{username}的个人账本", owner_id=user.id)
    db.session.add(ledger)
    db.session.flush()
    member = LedgerMember(ledger_id=ledger.id, user_id=user.id, role='manager')
    db.session.add(member)
    account = Account(name='默认账户', balance=0, account_type='cash', user_id=user.id, ledger_id=ledger.id)
    db.session.add(account)
    db.session.commit()
    token = generate_token(user.id)
    return jsonify({'success': True, 'token': token, 'user': {'id': user.id, 'username': user.username}}), 201
```

### 3.2 注册蓝图并适配 Session

**文件**：`cash_app/bootstrap.py` — 添加：

```python
from .routes_miniapp import miniapp_bp
app.register_blueprint(miniapp_bp)
```

### 3.3 为现有 API 添加 Token 兼容

**方案**：修改 `cash_app/auth.py` 中的 `login_required`，支持同时解析 Session 和 Token：

```python
# 在 cash_app/auth.py 中新增
def _get_user_from_token():
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else auth
    if not token:
        return None
    from .routes_miniapp import _tokens
    info = _tokens.get(token)
    if info and info['expires_at'] > time.time():
        user = User.query.get(info['user_id'])
        if user:
            g.user = user
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['self_view'] = True
            return user
    return None

# 修改 load_logged_in_user
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        _get_user_from_token()  # 尝试 Token 认证
    else:
        g.user = User.query.get(user_id)
```

### 3.4 建议新增的便捷 API

```python
# 批量查询：首页仪表盘所需数据聚合
@app.route('/api/miniapp/dashboard', methods=['GET'])
@token_required
def miniapp_dashboard():
    """首页聚合数据（一次请求完成首页渲染）"""
    # 当日收支、月度统计、最近交易、账户概览
    ...

# 图片上传
@app.route('/api/miniapp/upload', methods=['POST'])
@token_required
def miniapp_upload():
    """小程序图片上传（头像、凭证等）"""
    ...
```

---

## 四、设计规范与主题

### 4.1 设计 Token

```css
/* styles/variables.wxss — 设计变量 */
:root {
  /* 主色系 */
  --primary: #4361EE;
  --primary-light: #6C83F5;
  --primary-dark: #3451D1;
  --primary-bg: #EEF1FF;

  /* 语义色 */
  --income: #10B981;
  --income-bg: #D1FAE5;
  --expense: #EF4444;
  --expense-bg: #FEE2E2;
  --warning: #F59E0B;
  --warning-bg: #FEF3C7;

  /* 中性色 */
  --text-primary: #1F2937;
  --text-secondary: #6B7280;
  --text-tertiary: #9CA3AF;
  --border: #E5E7EB;
  --bg-page: #F3F4F6;
  --bg-card: #FFFFFF;

  /* 尺寸 */
  --radius-sm: 8rpx;
  --radius-md: 12rpx;
  --radius-lg: 16rpx;
  --radius-xl: 20rpx;
  --spacing-xs: 8rpx;
  --spacing-sm: 12rpx;
  --spacing-md: 16rpx;
  --spacing-lg: 24rpx;
  --spacing-xl: 32rpx;
}
```

### 4.2 排版规则

```
页面结构：
┌──────────────────────┐
│  自定义导航栏 (88rpx) │  ← 标题 + 右操作
├──────────────────────┤
│                      │
│  内容区域 (scroll)    │  ← 可滚动
│  ┌────────────────┐  │
│  │ 统计卡片        │  │
│  ├────────────────┤  │
│  │ 功能入口 / 列表 │  │
│  └────────────────┘  │
│                      │
├──────────────────────┤
│  底部Tab栏 (100rpx)  │  ← 首页/记账/报表/我的
└──────────────────────┘

列表项高度：120rpx（含上下间距）
卡片内边距：32rpx
字号体系：navi 36rpx / title 32rpx / body 28rpx / caption 24rpx
```

### 4.3 全局样式

```css
/* app.wxss */
page {
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: var(--bg-page);
  color: var(--text-primary);
  font-size: 28rpx;
  line-height: 1.6;
}

/* 卡片 */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin: var(--spacing-sm) var(--spacing-md);
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.04);
}

/* 按钮 */
.btn-primary {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: #fff;
  border-radius: var(--radius-md);
  padding: 20rpx 0;
  text-align: center;
  font-size: 32rpx;
  font-weight: 600;
  box-shadow: 0 4rpx 16rpx rgba(67, 110, 255, 0.3);
}

.btn-income {
  background: linear-gradient(135deg, var(--income) 0%, #059669 100%);
  color: #fff;
}

.btn-expense {
  background: linear-gradient(135deg, var(--expense) 0%, #DC2626 100%);
  color: #fff;
}
```

---

## 五、页面设计与实现

### 5.1 首页看板 (`pages/index/`)

```
┌──────────────────────┐
│  9月15日 星期日  ☁️   │  ← 日期 + 天气
├──────────────────────┤
│  ┌────────────────┐  │
│  │  本月结余       │  │
│  │  ¥ 12,580.00   │  │  ← 大号数字
│  │ 收入 ¥8,200     │  │
│  │ 支出 ¥2,580     │  │  ← 进度条
│  └────────────────┘  │
│                      │
│  今日概况             │
│  ┌──────┐ ┌──────┐  │
│  │ 收入  │ │ 支出  │  │  ← 小卡片
│  │¥200   │ │¥85    │  │
│  └──────┘ └──────┘  │
│                      │
│  快捷功能 (2x2 网格)  │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐│
│  │记 │ │扫 │ │智 │ │报│  │  ← 图标 + 文字
│  │一 │ │码 │ │能 │ │销 │  │
│  │笔 │ │付 │ │记 │ │管 │  │
│  │   │ │款 │ │账 │ │理 │  │
│  └──┘ └──┘ └──┘ └──┘│
│                      │
│  最近交易 (5条)       │
│  ┌────────────────┐  │
│  │🍜 餐饮    ¥35  │  │  ← 带图标分类
│  │🚇 交通    ¥5   │  │
│  │💊 医疗    ¥128 │  │
│  │💼 工资  ¥8000 │  │  ← 绿色表示收入
│  └────────────────┘  │
├──────────────────────┤
│  首页  记账  报表  我的│  ← TabBar
└──────────────────────┘
```

**核心逻辑**：

```javascript
// pages/index/index.js
Page({
  data: {
    today: {},        // 今日收支
    monthSummary: {}, // 月度汇总
    recentTx: [],     // 最近交易
    accounts: [],     // 账户快照
    loading: true
  },

  onLoad() {
    this.loadDashboard();
  },

  async loadDashboard() {
    this.setData({ loading: true });
    try {
      // 一次请求获取全部首页数据
      const res = await api.get('/api/miniapp/dashboard');
      this.setData({
        today: res.today,
        monthSummary: res.monthSummary,
        recentTx: res.recentTx.slice(0, 5),
        accounts: res.accounts,
        loading: false
      });
    } catch (e) {
      utils.showError(e);
      this.setData({ loading: false });
    }
  }
});
```

### 5.2 记一笔 (`pages/transaction-add/`)

```
┌──────────────────────┐
│  ← 返回     记一笔   │  ← 导航栏
├──────────────────────┤
│  ┌──────┐ ┌──────┐  │
│  │ 支出  │ │ 收入  │  │  ← 类型切换 Tab
│  └──────┘ └──────┘  │
│                      │
│        ¥ 0.00        │  ← 金额输入（大号）
│     ────────         │  ← 分隔线
│                      │
│  分类选择 (4列网格)   │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐│
│  │🍚│ │🚗│ │🛒│ │🎮││  ← Emoji 图标
│  │餐 │ │交 │ │购 │ │娱│  │
│  │饮 │ │通 │ │物 │ │乐│  │
│  ├──┤ ├──┤ ├──┤ ├──┤│
│  │🏠│ │📚│ │📞│ │➕││
│  │住 │ │教 │ │通 │ │更 ││
│  │房 │ │育 │ │讯 │ │多 ││
│  └──┘ └──┘ └──┘ └──┘│
│                      │
│  ┌────────────────┐  │
│  │ 账户: 默认账户  │  │  ← 选择器
│  ├────────────────┤  │
│  │ 日期: 今天      │  │
│  ├────────────────┤  │
│  │ 备注: 买奶茶    │  │  ← 输入框
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │    ✅ 确认记账  │  │  ← 主按钮
│  └────────────────┘  │
└──────────────────────┘
```

**样式关键点**：

```css
/* 金额输入区域 */
.amount-display {
  text-align: center;
  padding: 60rpx 0 30rpx;
}
.amount-input {
  font-size: 80rpx;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
  border: none;
  background: transparent;
  width: 100%;
}
.amount-unit {
  font-size: 36rpx;
  color: var(--text-secondary);
}

/* 分类网格 - 4列 */
.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  padding: var(--spacing-md);
}
.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 0;
  border-radius: var(--radius-md);
  background: var(--bg-page);
}
.category-item.active {
  background: var(--primary-bg);
  color: var(--primary);
}
.category-icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
}
.category-name {
  font-size: 24rpx;
  color: var(--text-secondary);
}
```

### 5.3 交易列表 (`pages/transactions/`)

```
┌──────────────────────┐
│  ← 返回    交易流水  │  │  ← 带搜索图标
├──────────────────────┤
│  ┌────────────────┐  │
│  │ 🔍 搜索交易...  │  │  ← 搜索框
│  └────────────────┘  │
│                      │
│  筛选栏               │
│  全部 │ 今天 │ 本周 │ 本月 │ 自定义  │  ← 横向滚动
│                      │
│  分组标题: 今天       │
│  ┌────────────────┐  │
│  │🍜 餐饮   -¥35  │  │  ← 左: 分类图标+备注
│  │     12:30 微信  │  │  ← 下: 时间+账户
│  ├────────────────┤  │
│  │🚇 交通    -¥5  │  │
│  │     08:45 现金  │  │
│  └────────────────┘  │
│                      │
│  分组标题: 9月14日    │
│  ...                 │
│                      │
│  加载更多...           │  ← 触底加载
└──────────────────────┘
```

**按日期分组逻辑**：

```javascript
function groupByDate(transactions) {
  const groups = {};
  transactions.forEach(tx => {
    const dateLabel = getDateLabel(tx.date); // "今天" / "9月14日"
    if (!groups[dateLabel]) groups[dateLabel] = [];
    groups[dateLabel].push(tx);
  });
  return Object.entries(groups).map(([date, items]) => ({ date, items }));
}
```

### 5.4 报表统计 (`pages/reports/`)

适配移动端，使用轻量图表代替 ECharts：

```
┌──────────────────────┐
│  ← 返回    统计分析  │
├──────────────────────┤
│  周期切换             │
│  周 │ 月 │ 季 │ 年 │自定义│  ← Tab
│                      │
│  概览卡片             │
│  ┌──────┐ ┌──────┐  │
│  │收入  │ │支出  │  │
│  │¥8,200│ │¥2,580│  │
│  └──────┘ └──────┘  │
│  结余: ¥5,620 ▲     │
│                      │
│  支出分类 TOP5       │
│  餐饮  ¥800  ███████░│  ← 横向进度条
│  交通  ¥350  ███░░░░░│
│  购物  ¥280  ██░░░░░░│
│  娱乐  ¥150  █░░░░░░░│
│  医疗  ¥128  █░░░░░░░│
│                      │
│  每日趋势 (迷你折线)  │
│  ╱╲╱ ╲╱╲╱╲╱╲        │  ← Canvas 绘制
│  ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲  │
│  1  5  10 15 20 25   │
│                      │
│  交易明细 (最近20条)  │
│  ┌────────────────┐  │
│  │🍜 餐饮  -¥35  │  │
│  │   2024-09-15   │  │
│  └────────────────┘  │
└──────────────────────┘
```

**使用小程序 Canvas 2D API 绘制迷你图表**（替代 ECharts，减小包体积）：

```javascript
// 简化折线图示例
function drawMiniChart(canvasId, data, color) {
  const query = wx.createSelectorQuery();
  query.select(`#${canvasId}`).fields({ node: true, size: true })
    .exec((res) => {
      const canvas = res[0].node;
      const ctx = canvas.getContext('2d');
      const width = res[0].width;
      const height = res[0].height;
      const padding = 20;

      const max = Math.max(...data);
      const min = Math.min(...data);
      const range = max - min || 1;
      const stepX = (width - padding * 2) / (data.length - 1);

      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.beginPath();
      data.forEach((val, i) => {
        const x = padding + i * stepX;
        const y = height - padding - ((val - min) / range) * (height - padding * 2);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
    });
}
```

### 5.5 智能记账 (`pages/smart-bookkeeping/`)

```
┌──────────────────────┐
│  ← 返回    智能记账  │
├──────────────────────┤
│                      │
│  ┌────────────────┐  │
│  │                │  │  ← 语音输入按钮 (大)
│  │     🎤         │  │
│  │  点击说话       │  │
│  └────────────────┘  │
│                      │
│  或输入文字           │
│  ┌────────────────┐  │
│  │ 今天中午吃饭花  │  │  ← 文本输入
│  │ 了35块          │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │  🤖 智能解析   │  │  ← 按钮
│  └────────────────┘  │
│                      │
│  解析结果预览          │
│  ┌────────────────┐  │
│  │ 🍜 餐饮 支出   │  │  ← 卡片预览
│  │ ¥ 35.00        │  │
│  │ 今天 12:30      │  │
│  ├────────────────┤  │
│  │ [确认]  [修改]  │  │
│  └────────────────┘  │
└──────────────────────┘
```

### 5.6 个人中心 (`pages/profile/`)

```
┌──────────────────────┐
│             个人中心  │
├──────────────────────┤
│  ┌────────────────┐  │
│  │  👤 用户名      │  │  ← 头像 + 昵称
│  │     微信号绑定   │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │ 📊 账户管理    │  │  → 箭头
│  ├────────────────┤  │
│  │ 📒 账本管理    │  │
│  ├────────────────┤  │
│  │ 💰 借贷管理    │  │
│  ├────────────────┤  │
│  │ 📋 周期账单    │  │
│  ├────────────────┤  │
│  │ 💳 报销管理    │  │
│  ├────────────────┤  │
│  │ 📈 资金变动    │  │
│  ├────────────────┤  │
│  │ 🔒 修改密码    │  │
│  ├────────────────┤  │
│  │ 🤖 AI 分析     │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │   退出登录      │  │  ← 红色按钮
│  └────────────────┘  │
├──────────────────────┤
│  首页  记账  报表  我的│
└──────────────────────┘
```

---

## 六、TabBar 与页面路由

### 6.1 app.json 配置

```json
{
  "pages": [
    "pages/index/index",
    "pages/transactions/transactions",
    "pages/reports/reports",
    "pages/profile/profile",
    "pages/login/login",
    "pages/transaction-add/transaction-add",
    "pages/transaction-edit/transaction-edit",
    "pages/accounts/accounts",
    "pages/ledgers/ledgers",
    "pages/budget/budget",
    "pages/loans/loans",
    "pages/reimbursement/reimbursement",
    "pages/recurring/recurring",
    "pages/smart-bookkeeping/smart-bookkeeping",
    "pages/ai-analysis/ai-analysis",
    "pages/change-password/change-password"
  ],
  "tabBar": {
    "color": "#9CA3AF",
    "selectedColor": "#4361EE",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "white",
    "list": [
      {
        "pagePath": "pages/index/index",
        "iconPath": "assets/icons/home.png",
        "selectedIconPath": "assets/icons/home-active.png",
        "text": "首页"
      },
      {
        "pagePath": "pages/transaction-add/transaction-add",
        "iconPath": "assets/icons/add.png",
        "selectedIconPath": "assets/icons/add-active.png",
        "text": "记账"
      },
      {
        "pagePath": "pages/reports/reports",
        "iconPath": "assets/icons/chart.png",
        "selectedIconPath": "assets/icons/chart-active.png",
        "text": "报表"
      },
      {
        "pagePath": "pages/profile/profile",
        "iconPath": "assets/icons/mine.png",
        "selectedIconPath": "assets/icons/mine-active.png",
        "text": "我的"
      }
    ]
  },
  "window": {
    "navigationBarBackgroundColor": "#FFFFFF",
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "线上记账",
    "navigationStyle": "custom",
    "backgroundColor": "#F3F4F6"
  },
  "usingComponents": {}
}
```

---

## 七、核心服务层

### 7.1 API 封装 (`services/api.js`)

```javascript
// services/api.js
const BASE_URL = 'https://your-domain.com'; // 生产环境域名

const request = (method, path, data = {}) => {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token');
    wx.request({
      url: BASE_URL + path,
      method: method,
      data: method === 'GET' ? data : JSON.stringify(data),
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        if (res.statusCode === 401 && path !== '/api/miniapp/login') {
          // Token 过期，跳转登录
          wx.removeStorageSync('token');
          wx.redirectTo({ url: '/pages/login/login' });
          reject(new Error('登录已过期'));
          return;
        }
        if (res.data.success === false) {
          reject(new Error(res.data.message || '请求失败'));
        } else {
          resolve(res.data);
        }
      },
      fail: (err) => {
        reject(new Error('网络错误，请检查网络连接'));
      }
    });
  });
};

// 便捷方法
export const api = {
  get: (path, params) => request('GET', path, params),
  post: (path, data) => request('POST', path, data),
  put: (path, data) => request('PUT', path, data),
  del: (path, data) => request('DELETE', path, data),
};
```

### 7.2 登录认证 (`services/auth.js`)

```javascript
// services/auth.js
import { api } from './api';

export const auth = {
  async login(username, password) {
    const res = await api.post('/api/miniapp/login', { username, password });
    wx.setStorageSync('token', res.token);
    wx.setStorageSync('user', res.user);
    return res;
  },

  async register(username, password) {
    const res = await api.post('/api/miniapp/register', { username, password });
    wx.setStorageSync('token', res.token);
    wx.setStorageSync('user', res.user);
    return res;
  },

  logout() {
    wx.removeStorageSync('token');
    wx.removeStorageSync('user');
    wx.removeStorageSync('cache');
    wx.redirectTo({ url: '/pages/login/login' });
  },

  isLoggedIn() {
    return !!wx.getStorageSync('token');
  },

  getUser() {
    return wx.getStorageSync('user') || null;
  }
};
```

### 7.3 缓存服务 (`services/cache.js`)

```javascript
// services/cache.js
const CACHE_PREFIX = 'cache_';
const CACHE_TTL = 5 * 60 * 1000; // 5分钟

export const cache = {
  set(key, data) {
    const item = { data, expires: Date.now() + CACHE_TTL };
    wx.setStorageSync(CACHE_PREFIX + key, item);
  },

  get(key) {
    const item = wx.getStorageSync(CACHE_PREFIX + key);
    if (!item) return null;
    if (Date.now() > item.expires) {
      wx.removeStorageSync(CACHE_PREFIX + key);
      return null;
    }
    return item.data;
  },

  clear() {
    const keys = wx.getStorageInfoSync().keys;
    keys.filter(k => k.startsWith(CACHE_PREFIX))
      .forEach(k => wx.removeStorageSync(k));
  }
};
```

---

## 八、组件实现

### 8.1 账本切换器 (`components/ledger-switcher/`)

```html
<!-- components/ledger-switcher/ledger-switcher.wxml -->
<view class="ledger-switcher" bind:tap="showPicker">
  <text class="ledger-name">{{currentLedger.name}}</text>
  <text class="ledger-arrow">▼</text>
</view>

<!-- 弹出选择面板 -->
<view class="picker-overlay" wx:if="{{showPicker}}" bind:tap="hidePicker">
  <view class="picker-panel" catch:tap="noop">
    <view class="picker-header">
      <text class="picker-title">切换账本</text>
      <text class="picker-close" bind:tap="hidePicker">✕</text>
    </view>
    <scroll-view scroll-y class="picker-list">
      <view 
        wx:for="{{ledgers}}" 
        wx:key="id"
        class="picker-item {{item.id === currentLedger.id ? 'active' : ''}}"
        bind:tap="selectLedger" 
        data-id="{{item.id}}"
      >
        <text class="item-name">{{item.name}}</text>
        <text class="item-role">{{roleMap[item.role]}}</text>
        <text class="item-check" wx:if="{{item.id === currentLedger.id}}">✓</text>
      </view>
    </scroll-view>
    <view class="picker-footer">
      <button bind:tap="goToLedgerManage">管理账本</button>
    </view>
  </view>
</view>
```

### 8.2 金额输入组件 (`components/amount-input/`)

```javascript
// components/amount-input/amount-input.js
Component({
  properties: {
    value: { type: String, value: '0.00' }
  },
  data: {
    display: '0.00',
    cursor: 0
  },
  methods: {
    inputDigit(e) {
      const digit = e.currentTarget.dataset.digit;
      let current = this.data.display.replace('.', '');
      if (digit === '.') {
        if (this.data.display.includes('.')) return;
        // 小数点后默认两位
        this.setData({ display: this.data.display + '.' });
        return;
      }
      if (digit === 'backspace') {
        const clean = this.data.display.replace('.', '');
        const newClean = clean.slice(0, -1) || '0';
        const int = newClean.slice(0, -2) || '0';
        const dec = newClean.slice(-2).padEnd(2, '0');
        this.setData({ display: `${int}.${dec}` });
        this.triggerEvent('change', { value: parseFloat(`${int}.${dec}`) });
        return;
      }
      // 追加数字
      let newStr = current + digit;
      // 限制15位
      if (newStr.length > 15) return;
      const int = newStr.slice(0, -2) || '0';
      const dec = newStr.slice(-2).padEnd(2, '0');
      const formatted = `${parseInt(int).toLocaleString()}.${dec}`;
      this.setData({ display: formatted });
      this.triggerEvent('change', { value: parseFloat(`${int}.${dec}`) });
    }
  }
});
```

---

## 九、微信 vs 支付宝适配

### 9.1 uni-app 方案（推荐）

使用 uni-app 开发，一份 Vue 代码编译到两端：

```vue
<!-- 以 Vue 单文件组件开发 -->
<template>
  <view class="page">
    <view class="card">
      <text class="amount">¥{{ amount }}</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return { amount: '0.00' }
  },
  onLoad() {
    // 生命周期 — 两端一致
  },
  methods: {
    async loadData() {
      const res = await uni.request({
        url: '/api/transactions',
        header: { Authorization: 'Bearer ' + uni.getStorageSync('token') }
      });
    }
  }
}
</script>

<style scoped>
/* 使用 rpx 单位，两端自动适配 */
.card { padding: 32rpx; }
</style>
```

**uni-app 目录结构**：
```
uni-miniapp/
├── src/
│   ├── pages/           # 页面
│   ├── components/      # 组件
│   ├── utils/           # 工具
│   ├── api.js           # API 封装
│   ├── App.vue          # 入口组件
│   └── main.js          # 入口 JS
├── manifest.json        # 应用配置
├── pages.json           # 路由配置（替代 app.json）
└── uni.scss             # 全局样式变量
```

### 9.2 原生开发适配要点

| 功能 | 微信 | 支付宝 |
|------|------|--------|
| 登录 | `wx.login()` + code | `my.getAuthCode()` + authCode |
| 用户信息 | `wx.getUserProfile()` | `my.getAuthUserInfo()` |
| 支付 | `wx.requestPayment()` | `my.tradePay()` |
| 请求 | `wx.request()` | `my.request()` |
| 本地存储 | `wx.setStorageSync()` | `my.setStorageSync()` |
| 路由 | `wx.navigateTo()` | `my.navigateTo()` |
| 条件编译 | `(#ifdef MP-WEIXIN)` | `(#ifdef MP-ALIPAY)` |

---

## 十、数据同步策略

### 10.1 离线缓存

```
首次加载 → 写入缓存
下次打开 → 读取缓存渲染 → 后台请求新数据 → 更新缓存 & 视图

缓存策略:
- 首页数据: 5分钟过期
- 分类列表: 30分钟过期  
- 交易列表: 不缓存（或仅缓存最近一页）
- 用户信息: 持久化（除非退出登录）
```

### 10.2 下拉刷新

```javascript
// 页面配置
{
  "enablePullDownRefresh": true,
  "backgroundColor": "#F3F4F6"
}

// 页面逻辑
Page({
  onPullDownRefresh() {
    Promise.all([
      this.loadDashboard(),
      this.loadCategories()
    ]).then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
```

---

## 十一、与网页版功能差异说明

| 功能 | 网页版 | 小程序 | 原因 |
|------|--------|--------|------|
| 导入 Excel/CSV | ✅ | ❌ | 小程序文件选择限制，如需保留可使用「扫码导入」或「从聊天文件导入」 |
| 导出下载 | ✅ | ❌ | 可改为「分享到微信」或「发送到邮箱」 |
| 管理后台 | ✅ | ❌ | 管理员功能保留在网页端 |
| 多币种汇率编辑 | ✅ | ✅ | 简化为仅展示换算结果 |
| 账本成员管理 | ✅ | ✅ | 简化界面，保留核心功能 |
| 借贷还款记录 | ✅ | ✅ | 简化表单，适配移动端 |

---

## 十二、开发与部署步骤

### Step 1: 后端适配（约 1 天）
1. 新建 `cash_app/routes_miniapp.py`，实现 Token 登录/注册
2. 修改 `auth.py` 的 `login_required`，支持 Token 认证
3. 新增聚合 API（如 `/api/miniapp/dashboard`）
4. 部署到服务器，配置 HTTPS

### Step 2: 搭建小程序项目（约 0.5 天）
1. 注册微信小程序 / 支付宝小程序开发者账号
2. 使用 uni-app 初始化项目
3. 配置 `pages.json` 路由、TabBar
4. 实现 API 封装层、登录认证

### Step 3: 核心页面开发（约 3-4 天）
1. 登录/注册页面（0.5天）
2. 首页看板（1天）
3. 记一笔（1天）
4. 交易列表（0.5天）
5. 个人中心（0.5天）

### Step 4: 功能页面开发（约 3-4 天）
1. 账户管理（0.5天）
2. 账本管理 + 成员（0.5天）
3. 预算管理（0.5天）
4. 借贷管理（0.5天）
5. 报销管理（0.5天）
6. 周期账单（0.5天）
7. 报表统计（1天）
8. 智能记账 + AI 分析（0.5天）

### Step 5: 优化与测试（约 1-2 天）
1. 离线缓存策略
2. 加载状态处理
3. 错误边界
4. 兼容性测试（微信/支付宝）

---

## 十三、关键代码：uni-app 版 pages.json

```json
{
  "pages": [
    {"path": "pages/index/index", "style": {"navigationStyle": "custom"}},
    {"path": "pages/transactions/transactions", "style": {"navigationBarTitleText": "交易流水"}},
    {"path": "pages/transaction-add/transaction-add", "style": {"navigationBarTitleText": "记一笔"}},
    {"path": "pages/transaction-edit/transaction-edit", "style": {"navigationBarTitleText": "编辑交易"}},
    {"path": "pages/reports/reports", "style": {"navigationBarTitleText": "统计分析"}},
    {"path": "pages/profile/profile", "style": {"navigationBarTitleText": "个人中心"}},
    {"path": "pages/accounts/accounts", "style": {"navigationBarTitleText": "账户管理"}},
    {"path": "pages/ledgers/ledgers", "style": {"navigationBarTitleText": "账本管理"}},
    {"path": "pages/budget/budget", "style": {"navigationBarTitleText": "预算管理"}},
    {"path": "pages/loans/loans", "style": {"navigationBarTitleText": "借贷管理"}},
    {"path": "pages/reimbursement/reimbursement", "style": {"navigationBarTitleText": "报销管理"}},
    {"path": "pages/recurring/recurring", "style": {"navigationBarTitleText": "周期账单"}},
    {"path": "pages/smart-bookkeeping/smart-bookkeeping", "style": {"navigationBarTitleText": "智能记账"}},
    {"path": "pages/ai-analysis/ai-analysis", "style": {"navigationBarTitleText": "AI 分析"}},
    {"path": "pages/change-password/change-password", "style": {"navigationBarTitleText": "修改密码"}},
    {"path": "pages/login/login", "style": {"navigationBarTitleText": "登录"}}
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "线上记账",
    "navigationBarBackgroundColor": "#FFFFFF",
    "backgroundColor": "#F3F4F6",
    "enablePullDownRefresh": true
  },
  "tabBar": {
    "color": "#9CA3AF",
    "selectedColor": "#4361EE",
    "backgroundColor": "#FFFFFF",
    "borderStyle": "white",
    "list": [
      {"pagePath": "pages/index/index", "text": "首页", "iconPath": "static/tab/home.png", "selectedIconPath": "static/tab/home-active.png"},
      {"pagePath": "pages/transaction-add/transaction-add", "text": "记账", "iconPath": "static/tab/add.png", "selectedIconPath": "static/tab/add-active.png"},
      {"pagePath": "pages/reports/reports", "text": "报表", "iconPath": "static/tab/chart.png", "selectedIconPath": "static/tab/chart-active.png"},
      {"pagePath": "pages/profile/profile", "text": "我的", "iconPath": "static/tab/mine.png", "selectedIconPath": "static/tab/mine-active.png"}
    ]
  }
}
```

---

## 十四、设计资源

### 分类 Emoji 映射表（用于小程序直观展示）

```javascript
// 用于分类图标展示
export const CATEGORY_ICONS = {
  // 支出分类
  '餐饮': '🍜', '交通': '🚇', '购物': '🛒', '娱乐': '🎮',
  '医疗': '💊', '住房': '🏠', '教育': '📚', '通讯': '📞',
  '其他支出': '📦',
  // 收入分类
  '工资': '💼', '奖金': '🏆', '投资收益': '📈', '兼职': '💻',
  '红包': '🧧', '报销收入': '📋', '其他收入': '💰',
};
```

### 配色参考

```
收入色 (green):   #10B981  → 背景 #D1FAE5
支出色 (red):     #EF4444  → 背景 #FEE2E2
品牌色 (blue):    #4361EE  → 背景 #EEF1FF
警告色 (amber):   #F59E0B  → 背景 #FEF3C7
```

---

## 十五、常见问题

### Q1: Session 和 Token 如何共存？
后端 `login_required` 装饰器先检查 Session（网页），再检查 `Authorization` 头（小程序），两种方式都设置 `g.user`。

### Q2: 小程序包体积超限怎么办？
- 使用网络图片代替本地图标（或使用 Emoji）
- 不要引入 ECharts，使用 Canvas 2D 自行绘制迷你图表
- 分包加载低频页面（借贷/报销/周期账单等放分包）

### Q3: 如何实现多端复用？
- 推荐 uni-app（Vue 3 + Vite），一套代码编译到微信/支付宝/百度/QQ/H5
- 条件编译处理平台差异：`(#ifdef MP-WEIXIN)` / `(#ifdef MP-ALIPAY)`

### Q4: 小程序支付的集成方式？
如果后续要接入支付：
```
微信支付: wx.requestPayment → 后端统一下单 → 用户确认 → 支付回调
支付宝:   my.tradePay      → 同上
```

### Q5: 与网页版共享域名？
小程序只支持 HTTPS 且需要配置白名单域名。建议：
- 使用二级域名：`api.your-domain.com`
- 在微信小程序后台配置 `request 合法域名`

---

> **总结**：本项目后端架构完善、API 覆盖全面，小程序端主要工作是：
> 1. 后端新增 Token 认证 + 小程序专有 API（~100 行代码）
> 2. 前端使用 uni-app 或原生框架开发小程序页面
> 3. 按移动端交互习惯重新设计布局（底部 Tab、卡片式、大号金额输入、横向滚动筛选等）
> 4. 核心业务逻辑完全复用现有后端，零重复开发
