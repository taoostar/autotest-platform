from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.module import Module
from app.models.audit import AuditLog

modules_bp = Blueprint('modules', __name__)


@modules_bp.route('/projects/<int:project_id>/modules', methods=['GET'])
@jwt_required()
def list_modules(project_id):
    """获取模块列表"""
    modules = Module.query.filter_by(project_id=project_id).order_by(Module.created_at.desc()).all()
    return jsonify([m.to_dict() for m in modules])


@modules_bp.route('/projects/<int:project_id>/modules', methods=['POST'])
@jwt_required()
def create_module(project_id):
    """创建模块"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '模块名称不能为空'}), 400

    # 验证项目存在
    from app.models.project import Project
    Project.query.get_or_404(project_id)

    module = Module(
        project_id=project_id,
        name=name,
        description=data.get('description', '')
    )
    db.session.add(module)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='module',
        resource_id=module.id,
        details={'name': name, 'project_id': project_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(module.to_dict()), 201


@modules_bp.route('/modules/<int:module_id>', methods=['GET'])
@jwt_required()
def get_module(module_id):
    """获取模块详情"""
    module = Module.query.get_or_404(module_id)
    return jsonify(module.to_dict(include_cases=True))


@modules_bp.route('/modules/<int:module_id>', methods=['PUT'])
@jwt_required()
def update_module(module_id):
    """更新模块"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    module = Module.query.get_or_404(module_id)

    if 'name' in data:
        module.name = data['name'].strip()
    if 'description' in data:
        module.description = data['description']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='module',
        resource_id=module.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(module.to_dict())


@modules_bp.route('/modules/<int:module_id>', methods=['DELETE'])
@jwt_required()
def delete_module(module_id):
    """删除模块"""
    current_user_id = int(get_jwt_identity())

    module = Module.query.get_or_404(module_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='module',
        resource_id=module.id,
        details={'name': module.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(module)
    db.session.commit()

    return jsonify({'message': '删除成功'})