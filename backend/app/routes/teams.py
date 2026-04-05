from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.team import Team, UserTeam
from app.models.audit import AuditLog

teams_bp = Blueprint('teams', __name__)


@teams_bp.route('', methods=['GET'])
@jwt_required()
def list_teams():
    """获取团队列表"""
    teams = Team.query.all()
    return jsonify([t.to_dict(include_members=True) for t in teams])


@teams_bp.route('', methods=['POST'])
@jwt_required()
def create_team():
    """创建团队"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '团队名称不能为空'}), 400

    team = Team(name=name, description=data.get('description', ''))
    db.session.add(team)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='team',
        resource_id=team.id,
        details={'name': name},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(team.to_dict()), 201


@teams_bp.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team(team_id):
    """获取团队详情"""
    team = Team.query.get_or_404(team_id)
    return jsonify(team.to_dict(include_members=True))


@teams_bp.route('/<int:team_id>', methods=['PUT'])
@jwt_required()
def update_team(team_id):
    """更新团队"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    team = Team.query.get_or_404(team_id)

    if 'name' in data:
        team.name = data['name'].strip()
    if 'description' in data:
        team.description = data['description']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='team',
        resource_id=team.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(team.to_dict())


@teams_bp.route('/<int:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    """删除团队"""
    current_user_id = int(get_jwt_identity())

    team = Team.query.get_or_404(team_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='team',
        resource_id=team.id,
        details={'name': team.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(team)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@teams_bp.route('/<int:team_id>/members', methods=['POST'])
@jwt_required()
def add_member(team_id):
    """添加团队成员"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    team = Team.query.get_or_404(team_id)
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id不能为空'}), 400

    from app.models.user import User
    user = User.query.get_or_404(user_id)

    # 检查是否已是成员
    if user in team.members:
        return jsonify({'error': '用户已是团队成员'}), 400

    team.members.append(user)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='add_member',
        resource_type='team',
        resource_id=team.id,
        details={'user_id': user_id, 'username': user.username},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(team.to_dict(include_members=True))


@teams_bp.route('/<int:team_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(team_id, user_id):
    """移除团队成员"""
    current_user_id = int(get_jwt_identity())

    team = Team.query.get_or_404(team_id)

    from app.models.user import User
    user = User.query.get_or_404(user_id)

    if user not in team.members:
        return jsonify({'error': '用户不是团队成员'}), 400

    team.members.remove(user)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='remove_member',
        resource_type='team',
        resource_id=team.id,
        details={'user_id': user_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': '移除成功'})