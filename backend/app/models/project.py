from datetime import datetime
from app import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = db.relationship('Team', back_populates='projects')
    modules = db.relationship('Module', back_populates='project', cascade='all, delete-orphan')
    plans = db.relationship('TestPlan', back_populates='project', cascade='all, delete-orphan')

    def to_dict(self, include_modules=False):
        data = {
            'id': self.id,
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_modules:
            data['modules'] = [m.to_dict() for m in self.modules]
        return data