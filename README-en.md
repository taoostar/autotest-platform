# AutoTest Platform

Enterprise-grade Automated Testing Platform

---

## Overview

AutoTest Platform is an enterprise-grade automated testing platform supporting multiple types of testing:
- Unit Testing
- API/Interface Testing
- UI Automation Testing (Web/App)
- Integration Testing
- Performance/Load Testing
- E2E End-to-End Testing

## Features

- **Multi-user & Team Collaboration** - Support for multiple users and team-based workflows
- **Test Case Management** - Online case management with version control
- **Distributed Test Execution** - Agent-based distributed execution mode
- **Scheduled Tasks & Webhook Triggers** - Cron-based scheduling and external trigger support
- **Real-time Logs & Performance Monitoring** - Live execution logs and resource monitoring
- **Complete Test Reports** - Comprehensive reporting with trend analysis

## Tech Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| Frontend | React 18 + Ant Design 5 | SPA application |
| Code Editor | Monaco Editor | VS Code editor component |
| Charts | ECharts | Trend and performance charts |
| Backend | Python Flask | RESTful API |
| Database | SQLite (default) | Data storage |
| Real-time | Flask-SocketIO | WebSocket communication |
| Task Queue | APScheduler + Redis | Task scheduling |

## Project Structure

```
autotest/
├── agent/                 # Agent client for distributed execution
│   ├── agent.py          # Main agent program
│   ├── executor.py       # Script executor
│   ├── collector.py      # Performance data collector
│   └── config.yaml      # Agent configuration
├── backend/              # Backend API service
│   ├── app/              # Flask application
│   │   ├── routes/       # API endpoints
│   │   ├── models/       # Database models
│   │   └── agents/       # WebSocket handlers
│   ├── run.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/             # Frontend React application
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── services/     # API and WebSocket services
│   │   └── components/    # Reusable components
│   └── package.json
├── e2e/                  # Playwright E2E tests
├── nginx/                # Nginx reverse proxy configuration
├── readme/               # Documentation
│   ├── 设计文档.md        # Design document (Chinese)
│   ├── 实施计划文档.md    # Implementation plan (Chinese)
│   └── 测试用例设计文档.md # Test case design (Chinese)
└── scripts/             # Utility scripts
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Redis (for message queue)
- Nginx (for reverse proxy)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`

### Agent Setup

```bash
cd agent
pip install -r requirements.txt
python agent.py config.yaml
```

### Nginx Reverse Proxy

```bash
# Copy and modify nginx configuration
sudo cp nginx/autotest.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/autotest.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Default credentials: `admin / admin123`

## Configuration

### Backend (backend/app/config.py)

- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - SQLite database path
- `REDIS_URL` - Redis connection URL
- `SOCKETIO_MESSAGE_QUEUE` - Redis queue for SocketIO

### Agent (agent/config.yaml)

- `agent_id` - Unique agent identifier
- `platform_url` - Platform backend URL
- `heartbeat_interval` - Heartbeat interval in seconds

## API Documentation

After starting the backend, visit:
- API Health: `http://localhost:5000/api/v1/health`
- Swagger Docs (if enabled): `http://localhost:5000/api/docs`

## WebSocket Events

**Agent Namespace (`/ws/agent`):**
- `task_assign` - Receive task assignment
- `task_complete` - Report task completion
- `heartbeat` - Send heartbeat

**Client Namespace (`/ws/client`):**
- `subscribe_task` - Subscribe to task logs
- `task_log` - Receive task log updates

## Development

```bash
# Run backend tests
cd backend
pytest

# Run agent tests
cd agent
pytest

# Run E2E tests
cd e2e
npx playwright test
```

## Deployment

1. Configure Nginx with SSL certificate
2. Set up Redis server
3. Initialize database with `python run.py`
4. Start backend service
5. Start frontend dev server or build for production
6. Start agent clients on execution machines

---

## License

MIT License
