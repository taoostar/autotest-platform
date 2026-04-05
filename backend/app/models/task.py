from datetime import datetime
from app import db


class TestTask(db.Model):
    __tablename__ = 'test_tasks'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    status = db.Column(db.String(20), default='pending')  # pending/running/success/failed/cancelled
    trigger_type = db.Column(db.String(20), default='manual')  # manual/schedule/webhook
    env_vars_override = db.Column(db.JSON, default=dict)
    timeout_override = db.Column(db.Integer)
    concurrency = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # 秒
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plan = db.relationship('TestPlan', back_populates='tasks')
    agent = db.relationship('Agent', back_populates='tasks')
    creator = db.relationship('User', foreign_keys=[created_by])
    results = db.relationship('TaskResult', back_populates='task', cascade='all, delete-orphan')
    performance_logs = db.relationship('PerformanceLog', back_populates='task', cascade='all, delete-orphan')

    def to_dict(self, include_results=False):
        data = {
            'id': self.id,
            'plan_id': self.plan_id,
            'agent_id': self.agent_id,
            'status': self.status,
            'trigger_type': self.trigger_type,
            'env_vars_override': self.env_vars_override or {},
            'timeout_override': self.timeout_override,
            'concurrency': self.concurrency,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration': self.duration,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_results:
            data['results'] = [r.to_dict() for r in self.results]
        return data


class TaskResult(db.Model):
    __tablename__ = 'task_results'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    status = db.Column(db.String(20))  # passed/failed/error/cancelled
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)
    exit_code = db.Column(db.Integer)
    error_type = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    stack_trace = db.Column(db.Text)
    screenshots = db.Column(db.JSON, default=list)
    log_path = db.Column(db.String(500))
    performance = db.Column(db.JSON)

    task = db.relationship('TestTask', back_populates='results')
    case = db.relationship('TestCase', back_populates='results')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'case_id': self.case_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration': self.duration,
            'exit_code': self.exit_code,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'screenshots': self.screenshots or [],
            'log_path': self.log_path,
            'performance': self.performance
        }


class PerformanceLog(db.Model):
    __tablename__ = 'performance_logs'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('test_tasks.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_percent = db.Column(db.Float)
    memory_percent = db.Column(db.Float)
    io_wait = db.Column(db.Float)
    fd_count = db.Column(db.Integer)

    task = db.relationship('TestTask', back_populates='performance_logs')
    agent = db.relationship('Agent')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'io_wait': self.io_wait,
            'fd_count': self.fd_count
        }