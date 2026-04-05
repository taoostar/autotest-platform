from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.project import Project
from app.models.audit import AuditLog

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """获取项目列表"""
    team_id = request.args.get('team_id', type=int)

    query = Project.query
    if team_id:
        query = query.filter_by(team_id=team_id)

    projects = query.order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """创建项目"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    team_id = data.get('team_id')

    if not name:
        return jsonify({'error': '项目名称不能为空'}), 400
    if not team_id:
        return jsonify({'error': 'team_id不能为空'}), 400

    # 验证团队存在
    from app.models.team import Team
    Team.query.get_or_404(team_id)

    project = Project(
        team_id=team_id,
        name=name,
        description=data.get('description', '')
    )
    db.session.add(project)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='project',
        resource_id=project.id,
        details={'name': name, 'team_id': team_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(project.to_dict()), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """获取项目详情"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict(include_modules=True))


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """更新项目"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    project = Project.query.get_or_404(project_id)

    if 'name' in data:
        project.name = data['name'].strip()
    if 'description' in data:
        project.description = data['description']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='project',
        resource_id=project.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(project.to_dict())


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """删除项目"""
    current_user_id = int(get_jwt_identity())

    project = Project.query.get_or_404(project_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='project',
        resource_id=project.id,
        details={'name': project.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(project)
    db.session.commit()

    return jsonify({'message': '删除成功'})