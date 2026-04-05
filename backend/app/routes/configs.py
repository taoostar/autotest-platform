from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.config import SystemConfig
from app.models.env import EnvVariable
from app.models.audit import AuditLog

configs_bp = Blueprint('configs', __name__)


# 系统配置
@configs_bp.route('', methods=['GET'])
@jwt_required()
def get_configs():
    """获取所有系统配置"""
    configs = SystemConfig.query.all()
    return jsonify({c.key: c.value for c in configs})


@configs_bp.route('', methods=['PUT'])
@jwt_required()
def update_configs():
    """更新系统配置"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    for key, value in data.items():
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            db.session.add(config)

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='system_config',
        details={'keys': list(data.keys())},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': '更新成功'})


# 环境变量
@configs_bp.route('/env-vars', methods=['GET'])
@jwt_required()
def list_env_vars():
    """获取环境变量列表"""
    scope_type = request.args.get('scope_type', 'global')
    scope_id = request.args.get('scope_id', type=int)

    query = EnvVariable.query

    if scope_type:
        query = query.filter_by(scope_type=scope_type)
    if scope_id:
        query = query.filter_by(scope_id=scope_id)

    env_vars = query.all()
    return jsonify([e.to_dict() for e in env_vars])


@configs_bp.route('/env-vars', methods=['POST'])
@jwt_required()
def create_env_var():
    """创建环境变量"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    scope_type = data.get('scope_type', 'global')
    key = data.get('key', '').strip()
    value = data.get('value', '')

    if not key:
        return jsonify({'error': 'key不能为空'}), 400

    scope_id = data.get('scope_id') if scope_type == 'project' else None

    env_var = EnvVariable(
        scope_type=scope_type,
        scope_id=scope_id,
        key=key,
        value=value
    )
    db.session.add(env_var)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='env_variable',
        resource_id=env_var.id,
        details={'key': key},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(env_var.to_dict()), 201


@configs_bp.route('/env-vars/<int:var_id>', methods=['PUT'])
@jwt_required()
def update_env_var(var_id):
    """更新环境变量"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    env_var = EnvVariable.query.get_or_404(var_id)

    if 'value' in data:
        env_var.value = data['value']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='env_variable',
        resource_id=var_id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(env_var.to_dict())


@configs_bp.route('/env-vars/<int:var_id>', methods=['DELETE'])
@jwt_required()
def delete_env_var(var_id):
    """删除环境变量"""
    current_user_id = int(get_jwt_identity())

    env_var = EnvVariable.query.get_or_404(var_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='env_variable',
        resource_id=var_id,
        details={'key': env_var.key},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(env_var)
    db.session.commit()

    return jsonify({'message': '删除成功'})