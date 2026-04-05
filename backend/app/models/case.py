from datetime import datetime
from app import db


class TestCase(db.Model):
    __tablename__ = 'test_cases'

    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.JSON, default=list)  # 标签列表
    priority = db.Column(db.Integer, default=3)  # 1-5, 1最高
    timeout = db.Column(db.Integer, default=60)  # 秒
    retry = db.Column(db.Integer, default=0)  # 重试次数
    script_type = db.Column(db.String(20), default='python')  # python/shell/js
    current_version = db.Column(db.String(20), default='v1.0.0')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    module = db.relationship('Module', back_populates='cases')
    creator = db.relationship('User', foreign_keys=[created_by])
    versions = db.relationship('CaseVersion', back_populates='case', cascade='all, delete-orphan',
                               order_by='desc(CaseVersion.created_at)')
    plan_cases = db.relationship('TestPlanCase', back_populates='case', cascade='all, delete-orphan')
    results = db.relationship('TaskResult', back_populates='case', cascade='all, delete-orphan')

    # 获取最新版本的代码
    def get_latest_code(self):
        latest = CaseVersion.query.filter_by(case_id=self.id, is_latest=True).first()
        return latest.code_content if latest else ''

    def to_dict(self, include_code=False):
        data = {
            'id': self.id,
            'module_id': self.module_id,
            'name': self.name,
            'description': self.description,
            'tags': self.tags or [],
            'priority': self.priority,
            'timeout': self.timeout,
            'retry': self.retry,
            'script_type': self.script_type,
            'current_version': self.current_version,
            'created_by': self.created_by,
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_code:
            data['code'] = self.get_latest_code()
        return data


class CaseVersion(db.Model):
    __tablename__ = 'case_versions'

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    code_content = db.Column(db.Text, nullable=False)
    is_latest = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    case = db.relationship('TestCase', back_populates='versions')
    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'version': self.version,
            'is_latest': self.is_latest,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }