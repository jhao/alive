# GuardianMe (守护么)

跨平台安全守护应用（Web / iOS / Android）+ Flask 后端 MVP。

## 项目结构

- `backend/` Flask + SQLAlchemy API
- `app/` Expo (React Native) 单代码库，支持 iOS / Android / Web

## 快速启动

### 1) 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

默认监听 `http://127.0.0.1:5000`。

### 2) 启动前端

```bash
cd app
npm install
npm run start
```

- 输入 `w` 打开 Web
- 输入 `i` 打开 iOS 模拟器（macOS + Xcode）
- 输入 `a` 打开 Android 模拟器

## MVP 功能覆盖

- 用户注册（邮箱 + 昵称）
- 每日签到（记录最后签到时间）
- 紧急联系人管理（新增/列表）
- 生命体征上报（心率）
- 异常判定（低心率/无心率）
- 通知任务落库（模拟邮件/SMS/IM 多通道）
- 家属看板（按用户邮箱查询状态）

## 后续迭代建议

- JWT 鉴权 + 第三方登录
- APNs/FCM 推送、Twilio/阿里云短信
- HealthKit / Google Fit / 手环 SDK 接入
- OpenClaw agent 服务化集成
- 订阅计费、规则引擎、隐私合规增强
