from datetime import datetime
import uuid
from app import db


class Webhook(db.Model):
    __tablename__ = 'webhooks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(64), unique=True, default=lambda: str(uuid.uuid4()).replace('-', ''))
    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = db.relationship('TestPlan')
    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'token': self.token,
            'plan_id': self.plan_id,
            'trigger_url': f'/api/v1/webhook/trigger/{self.token}',
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }