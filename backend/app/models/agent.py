from datetime import datetime
from app import db


class Agent(db.Model):
    __tablename__ = 'agents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(200))
    ip_address = db.Column(db.String(50))
    os_type = db.Column(db.String(20))  # linux/windows/mac
    status = db.Column(db.String(20), default='offline')  # online/offline
    current_load = db.Column(db.Float, default=0)
    labels = db.Column(db.JSON, default=list)
    last_heartbeat = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('TestTask', back_populates='agent')
    groups = db.relationship('AgentGroup', secondary='agent_group_members', back_populates='agents')
    performance_logs = db.relationship('PerformanceLog', back_populates='agent')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'os_type': self.os_type,
            'status': self.status,
            'current_load': self.current_load,
            'labels': self.labels or [],
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentGroup(db.Model):
    __tablename__ = 'agent_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    agents = db.relationship('Agent', secondary='agent_group_members', back_populates='groups')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentGroupMembership(db.Model):
    __tablename__ = 'agent_group_members'

    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('agent_groups.id'), primary_key=True)