from datetime import datetime
from app import db


class TestPlan(db.Model):
    __tablename__ = 'test_plans'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    env_vars = db.Column(db.JSON, default=dict)  # 环境变量
    case_order = db.Column(db.JSON, default=list)  # 用例顺序
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = db.relationship('Project', back_populates='plans')
    creator = db.relationship('User', foreign_keys=[created_by])
    plan_cases = db.relationship('TestPlanCase', back_populates='plan', cascade='all, delete-orphan')
    tasks = db.relationship('TestTask', back_populates='plan')

    def to_dict(self, include_cases=False):
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'env_vars': self.env_vars or {},
            'case_order': self.case_order or [],
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_cases:
            plan_cases = TestPlanCase.query.filter_by(plan_id=self.id).order_by(TestPlanCase.order_index).all()
            data['cases'] = [pc.case.to_dict() for pc in plan_cases if pc.case]
        return data


class TestPlanCase(db.Model):
    __tablename__ = 'test_plan_cases'

    plan_id = db.Column(db.Integer, db.ForeignKey('test_plans.id'), primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), primary_key=True)
    order_index = db.Column(db.Integer, default=0)

    plan = db.relationship('TestPlan', back_populates='plan_cases')
    case = db.relationship('TestCase', back_populates='plan_cases')