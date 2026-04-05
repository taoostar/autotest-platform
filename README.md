# AutoTest Platform

企业级自动化测试平台

---

## 项目概述

AutoTest Platform 是一个企业级自动化测试平台，支持多种测试类型：
- 单元测试
- API/接口测试
- UI 自动化测试 (Web/App)
- 集成测试
- 性能/压力测试
- E2E 端到端测试

## 核心功能

- **多用户多团队协作** - 支持多用户和团队工作流
- **测试用例管理** - 在线用例管理，支持版本控制
- **分布式测试执行** - 基于 Agent 的分布式执行模式
- **定时任务与 Webhook** - Cron 调度和外部触发器支持
- **实时日志与性能监控** - 实时执行日志和资源监控
- **完整测试报告** - 完整的报告和趋势分析

## 技术栈

| 层级 | 技术选型 | 说明 |
|-----|---------|------|
| 前端框架 | React 18 + Ant Design 5 | SPA 应用 |
| 代码编辑器 | Monaco Editor | VS Code 编辑器组件 |
| 图表库 | ECharts | 趋势和性能图表 |
| 后端框架 | Python Flask | RESTful API |
| 数据库 | SQLite (默认) | 数据存储 |
| 实时通信 | Flask-SocketIO | WebSocket 通信 |
| 任务队列 | APScheduler + Redis | 任务调度 |

## 项目结构

```
autotest/
├── agent/                 # Agent 客户端
│   ├── agent.py          # Agent 主程序
│   ├── executor.py        # 脚本执行器
│   ├── collector.py      # 性能数据采集
│   └── config.yaml      # Agent 配置
├── backend/              # 后端 API 服务
│   ├── app/              # Flask 应用
│   │   ├── routes/       # API 端点
│   │   ├── models/       # 数据模型
│   │   └── agents/       # WebSocket 处理器
│   ├── run.py            # 应用入口
│   └── requirements.txt   # Python 依赖
├── frontend/             # 前端 React 应用
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   ├── services/      # API 和 WebSocket 服务
│   │   └── components/    # 可复用组件
│   └── package.json
├── e2e/                  # Playwright E2E 测试
├── nginx/                # Nginx 反向代理配置
├── readme/               # 文档目录
│   ├── 设计文档.md        # 完整设计文档
│   ├── 实施计划文档.md    # 实施计划
│   └── 测试用例设计文档.md # 测试用例设计
└── scripts/             # 工具脚本
```

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- Redis (用于消息队列)
- Nginx (用于反向代理)

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端将在 `http://localhost:5000` 启动

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动

### Agent 启动

```bash
cd agent
pip install -r requirements.txt
python agent.py config.yaml
```

### Nginx 反向代理

```bash
# 复制并修改 Nginx 配置
sudo cp nginx/autotest.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/autotest.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

默认账号密码：`admin / admin123`

## 配置说明

### 后端配置 (backend/app/config.py)

- `SECRET_KEY` - Flask 密钥
- `DATABASE_URL` - SQLite 数据库路径
- `REDIS_URL` - Redis 连接 URL
- `SOCKETIO_MESSAGE_QUEUE` - SocketIO 的 Redis 队列

### Agent 配置 (agent/config.yaml)

- `agent_id` - 唯一标识符
- `platform_url` - 平台后端 URL
- `heartbeat_interval` - 心跳间隔（秒）

## API 文档

后端启动后访问：
- API 健康检查：`http://localhost:5000/api/v1/health`

## WebSocket 事件

**Agent 命名空间 (`/ws/agent`):**
- `task_assign` - 接收任务分配
- `task_complete` - 上报任务完成
- `heartbeat` - 发送心跳

**客户端命名空间 (`/ws/client`):**
- `subscribe_task` - 订阅任务日志
- `task_log` - 接收任务日志更新

## 开发

```bash
# 运行后端测试
cd backend
pytest

# 运行 Agent 测试
cd agent
pytest

# 运行 E2E 测试
cd e2e
npx playwright test
```

## 部署说明

1. 配置 Nginx SSL 证书
2. 设置 Redis 服务器
3. 初始化数据库
4. 启动后端服务
5. 启动前端开发服务器或构建生产版本
6. 在执行机器上启动 Agent 客户端

---

## License

MIT License
