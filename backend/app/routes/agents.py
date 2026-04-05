from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.agent import Agent, AgentGroup, AgentGroupMembership
from app.models.audit import AuditLog

agents_bp = Blueprint('agents', __name__)


@agents_bp.route('', methods=['GET'])
@jwt_required()
def list_agents():
    """获取Agent列表"""
    status = request.args.get('status', '')
    os_type = request.args.get('os_type', '')
    group_id = request.args.get('group_id', type=int)

    query = Agent.query

    if status:
        query = query.filter_by(status=status)
    if os_type:
        query = query.filter_by(os_type=os_type)
    if group_id:
        query = query.join(AgentGroupMembership).filter(AgentGroupMembership.group_id == group_id)

    agents = query.all()
    return jsonify([a.to_dict() for a in agents])


@agents_bp.route('/<int:agent_id>', methods=['GET'])
@jwt_required()
def get_agent(agent_id):
    """获取Agent详情"""
    agent = Agent.query.get_or_404(agent_id)
    data = agent.to_dict()
    data['groups'] = [g.to_dict() for g in agent.groups]
    return jsonify(data)


@agents_bp.route('/<int:agent_id>', methods=['PUT'])
@jwt_required()
def update_agent(agent_id):
    """更新Agent信息"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    agent = Agent.query.get_or_404(agent_id)

    if 'name' in data:
        agent.name = data['name']
    if 'labels' in data:
        agent.labels = data['labels']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='agent',
        resource_id=agent.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(agent.to_dict())


@agents_bp.route('/<int:agent_id>', methods=['DELETE'])
@jwt_required()
def delete_agent(agent_id):
    """删除Agent"""
    current_user_id = int(get_jwt_identity())

    agent = Agent.query.get_or_404(agent_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='agent',
        resource_id=agent.id,
        details={'name': agent.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(agent)
    db.session.commit()

    return jsonify({'message': '删除成功'})


# Agent分组管理
@agents_bp.route('/groups', methods=['GET'])
@jwt_required()
def list_groups():
    """获取分组列表"""
    groups = AgentGroup.query.all()
    return jsonify([g.to_dict() for g in groups])


@agents_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    """创建分组"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '分组名称不能为空'}), 400

    group = AgentGroup(
        name=name,
        description=data.get('description', '')
    )
    db.session.add(group)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='agent_group',
        resource_id=group.id,
        details={'name': name},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(group.to_dict()), 201


@agents_bp.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    """更新分组"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    group = AgentGroup.query.get_or_404(group_id)

    if 'name' in data:
        group.name = data['name'].strip()
    if 'description' in data:
        group.description = data['description']

    db.session.commit()

    return jsonify(group.to_dict())


@agents_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    """删除分组"""
    current_user_id = int(get_jwt_identity())

    group = AgentGroup.query.get_or_404(group_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='agent_group',
        resource_id=group.id,
        details={'name': group.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(group)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@agents_bp.route('/groups/<int:group_id>/agents', methods=['POST'])
@jwt_required()
def add_agent_to_group(group_id):
    """添加Agent到分组"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    group = AgentGroup.query.get_or_404(group_id)
    agent_id = data.get('agent_id')

    if not agent_id:
        return jsonify({'error': 'agent_id不能为空'}), 400

    agent = Agent.query.get_or_404(agent_id)

    # 检查是否已在分组中
    if agent in group.agents:
        return jsonify({'error': 'Agent已在分组中'}), 400

    group.agents.append(agent)
    db.session.commit()

    return jsonify({'message': '添加成功'})


@agents_bp.route('/groups/<int:group_id>/agents/<int:agent_id>', methods=['DELETE'])
@jwt_required()
def remove_agent_from_group(group_id, agent_id):
    """从分组移除Agent"""
    current_user_id = int(get_jwt_identity())

    group = AgentGroup.query.get_or_404(group_id)
    agent = Agent.query.get_or_404(agent_id)

    if agent not in group.agents:
        return jsonify({'error': 'Agent不在分组中'}), 400

    group.agents.remove(agent)
    db.session.commit()

    return jsonify({'message': '移除成功'})