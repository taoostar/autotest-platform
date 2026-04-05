from datetime import datetime
from app import db


class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), nullable=False)
    cron_expression = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(50), default='Asia/Shanghai')
    enabled = db.Column(db.Boolean, default=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = db.relationship('TestPlan')
    agent = db.relationship('Agent')
    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'cron_expression': self.cron_expression,
            'timezone': self.timezone,
            'enabled': self.enabled,
            'agent_id': self.agent_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }