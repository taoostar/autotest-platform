from datetime import datetime
from app import db


class EnvVariable(db.Model):
    __tablename__ = 'env_variables'

    id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.String(20), nullable=False)  # global/project
    scope_id = db.Column(db.Integer)  # project_id when scope_type is project
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('scope_type', 'scope_id', 'key', name='uq_env_scope_key'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'scope_type': self.scope_type,
            'scope_id': self.scope_id,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }