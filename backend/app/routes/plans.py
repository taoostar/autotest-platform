from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.plan import TestPlan, TestPlanCase
from app.models.audit import AuditLog

plans_bp = Blueprint('plans', __name__)


@plans_bp.route('/projects/<int:project_id>/plans', methods=['GET'])
@jwt_required()
def list_plans(project_id):
    """获取测试计划列表"""
    plans = TestPlan.query.filter_by(project_id=project_id).order_by(TestPlan.created_at.desc()).all()
    return jsonify([p.to_dict() for p in plans])


@plans_bp.route('/projects/<int:project_id>/plans', methods=['POST'])
@jwt_required()
def create_plan(project_id):
    """创建测试计划"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '计划名称不能为空'}), 400

    # 验证项目存在
    from app.models.project import Project
    Project.query.get_or_404(project_id)

    plan = TestPlan(
        project_id=project_id,
        name=name,
        description=data.get('description', ''),
        env_vars=data.get('env_vars', {}),
        created_by=current_user_id
    )
    db.session.add(plan)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='plan',
        resource_id=plan.id,
        details={'name': name},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(plan.to_dict()), 201


@plans_bp.route('/plans/<int:plan_id>', methods=['GET'])
@jwt_required()
def get_plan(plan_id):
    """获取计划详情"""
    plan = TestPlan.query.get_or_404(plan_id)
    return jsonify(plan.to_dict(include_cases=True))


@plans_bp.route('/plans/<int:plan_id>', methods=['PUT'])
@jwt_required()
def update_plan(plan_id):
    """更新测试计划"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    plan = TestPlan.query.get_or_404(plan_id)

    if 'name' in data:
        plan.name = data['name'].strip()
    if 'description' in data:
        plan.description = data['description']
    if 'env_vars' in data:
        plan.env_vars = data['env_vars']
    if 'collect_performance' in data:
        plan.collect_performance = data['collect_performance']
    if 'process_keyword' in data:
        plan.process_keyword = data['process_keyword']

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='plan',
        resource_id=plan.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(plan.to_dict())


@plans_bp.route('/plans/<int:plan_id>', methods=['DELETE'])
@jwt_required()
def delete_plan(plan_id):
    """删除测试计划"""
    current_user_id = int(get_jwt_identity())

    plan = TestPlan.query.get_or_404(plan_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='plan',
        resource_id=plan.id,
        details={'name': plan.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(plan)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@plans_bp.route('/plans/<int:plan_id>/cases', methods=['PUT'])
@jwt_required()
def update_plan_cases(plan_id):
    """更新计划用例"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    plan = TestPlan.query.get_or_404(plan_id)
    case_ids = data.get('case_ids', [])

    # 删除旧的关联
    TestPlanCase.query.filter_by(plan_id=plan_id).delete()

    # 创建新的关联
    for idx, case_id in enumerate(case_ids):
        pc = TestPlanCase(
            plan_id=plan_id,
            case_id=case_id,
            order_index=idx
        )
        db.session.add(pc)

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='plan_cases',
        resource_id=plan_id,
        details={'case_ids': case_ids},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(plan.to_dict(include_cases=True))


@plans_bp.route('/plans/<int:plan_id>/copy', methods=['POST'])
@jwt_required()
def copy_plan(plan_id):
    """复制测试计划"""
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    original = TestPlan.query.get_or_404(plan_id)

    # 创建副本
    new_plan = TestPlan(
        project_id=original.project_id,
        name=f"{original.name} (副本)",
        description=original.description,
        env_vars=original.env_vars,
        created_by=current_user_id
    )
    db.session.add(new_plan)
    db.session.flush()

    # 复制用例关联
    old_cases = TestPlanCase.query.filter_by(plan_id=plan_id).all()
    for pc in old_cases:
        new_pc = TestPlanCase(
            plan_id=new_plan.id,
            case_id=pc.case_id,
            order_index=pc.order_index
        )
        db.session.add(new_pc)

    db.session.commit()

    return jsonify(new_plan.to_dict(include_cases=True)), 201