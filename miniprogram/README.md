# miniprogram (uni-app)

这是根据 `miniprogram-guide.md` 落地的 uni-app 小程序实现，已对接当前 Flask 后端接口。

## 已实现（页面）

- 认证：`login`、`register`
- 首页看板：`index`
- 交易：`transactions`、`transaction-add`、`transaction-detail`、`transaction-edit`
- 账户：`accounts`
- 账本与成员：`ledgers`、`ledger-members`
- 预算：`budget`
- 借贷：`loans`、`loan-add`
- 报销：`reimbursement`
- 周期账单：`recurring`、`recurring-add`
- 报表：`reports`
- 智能记账与 AI：`smart-bookkeeping`、`ai-analysis`
- 个人中心：`profile`、`change-password`、`about`

## 目录

- `pages/` 全功能页面
- `components/` 公共组件（`ledger-switcher`、`amount-input`）
- `services/` API 封装与认证服务
- `store/` token + 用户状态
- `styles/` 全局变量与通用样式

## 联调步骤

1. 启动 Flask 后端（默认 `http://127.0.0.1:8080`）。
2. 用 HBuilderX 导入 `miniprogram/`。
3. H5 预览默认端口 `http://localhost:8090`。
4. 运行到微信开发者工具（或 web 预览）进行调试。

如果后端地址不是 `127.0.0.1:8080`，修改 `services/api.js` 中 `BASE_URL` 即可。
