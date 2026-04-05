from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.case import TestCase, CaseVersion
from app.models.audit import AuditLog
import zipfile
import io

cases_bp = Blueprint('cases', __name__)


@cases_bp.route('/modules/<int:module_id>/cases', methods=['GET'])
@jwt_required()
def list_cases(module_id):
    """获取用例列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    tags = request.args.get('tags', '')  # 逗号分隔
    priority = request.args.get('priority', type=int)
    favorites = request.args.get('favorites', '').lower() == 'true'
    keyword = request.args.get('keyword', '')

    query = TestCase.query.filter_by(module_id=module_id)

    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        query = query.filter(TestCase.tags.overlap(tag_list))

    if priority:
        query = query.filter_by(priority=priority)

    if favorites:
        query = query.filter_by(is_favorite=True)

    if keyword:
        query = query.filter(TestCase.name.contains(keyword))

    pagination = query.order_by(TestCase.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'cases': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@cases_bp.route('/modules/<int:module_id>/cases', methods=['POST'])
@jwt_required()
def create_case(module_id):
    """创建用例"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '用例名称不能为空'}), 400

    code = data.get('code', '')

    # 验证模块存在
    from app.models.module import Module
    Module.query.get_or_404(module_id)

    case = TestCase(
        module_id=module_id,
        name=name,
        description=data.get('description', ''),
        tags=data.get('tags', []),
        priority=data.get('priority', 3),
        timeout=data.get('timeout', 60),
        retry=data.get('retry', 0),
        script_type=data.get('script_type', 'python'),
        current_version='v1.0.0',
        created_by=current_user_id
    )
    db.session.add(case)
    db.session.flush()  # 获取ID

    # 创建初始版本
    version = CaseVersion(
        case_id=case.id,
        version='v1.0.0',
        code_content=code,
        is_latest=True,
        created_by=current_user_id
    )
    db.session.add(version)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='case',
        resource_id=case.id,
        details={'name': name, 'module_id': module_id},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(case.to_dict(include_code=True)), 201


@cases_bp.route('/cases/<int:case_id>', methods=['GET'])
@jwt_required()
def get_case(case_id):
    """获取用例详情"""
    case = TestCase.query.get_or_404(case_id)
    return jsonify(case.to_dict(include_code=True))


@cases_bp.route('/cases/<int:case_id>', methods=['PUT'])
@jwt_required()
def update_case(case_id):
    """更新用例（创建新版本）"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    case = TestCase.query.get_or_404(case_id)

    # 更新基本信息
    if 'name' in data:
        case.name = data['name'].strip()
    if 'description' in data:
        case.description = data['description']
    if 'tags' in data:
        case.tags = data['tags']
    if 'priority' in data:
        case.priority = data['priority']
    if 'timeout' in data:
        case.timeout = data['timeout']
    if 'retry' in data:
        case.retry = data['retry']
    if 'script_type' in data:
        case.script_type = data['script_type']

    # 如果代码有变化，创建新版本
    if 'code' in data and data['code']:
        # 递增版本号
        current_ver = case.current_version
        parts = current_ver.lstrip('v').split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        new_version = 'v' + '.'.join(parts)

        # 取消旧版本的最新标记
        CaseVersion.query.filter_by(case_id=case.id, is_latest=True).update({'is_latest': False})

        # 创建新版本
        version = CaseVersion(
            case_id=case.id,
            version=new_version,
            code_content=data['code'],
            is_latest=True,
            created_by=current_user_id
        )
        db.session.add(version)
        case.current_version = new_version

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='case',
        resource_id=case.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(case.to_dict(include_code=True))


@cases_bp.route('/cases/<int:case_id>', methods=['DELETE'])
@jwt_required()
def delete_case(case_id):
    """删除用例"""
    current_user_id = int(get_jwt_identity())

    case = TestCase.query.get_or_404(case_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='case',
        resource_id=case.id,
        details={'name': case.name},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(case)
    db.session.commit()

    return jsonify({'message': '删除成功'})


@cases_bp.route('/cases/<int:case_id>/versions', methods=['GET'])
@jwt_required()
def list_versions(case_id):
    """获取版本历史"""
    versions = CaseVersion.query.filter_by(case_id=case_id).order_by(CaseVersion.created_at.desc()).all()
    return jsonify([v.to_dict() for v in versions])


@cases_bp.route('/cases/<int:case_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_version(case_id, version_id):
    """获取指定版本"""
    version = CaseVersion.query.filter_by(id=version_id, case_id=case_id).first_or_404()
    return jsonify({
        **version.to_dict(),
        'code_content': version.code_content
    })


@cases_bp.route('/cases/<int:case_id>/rollback/<int:version_id>', methods=['POST'])
@jwt_required()
def rollback_case(case_id, version_id):
    """回滚到指定版本"""
    data = request.get_json() or {}
    current_user_id = int(get_jwt_identity())

    case = TestCase.query.get_or_404(case_id)
    old_version = CaseVersion.query.filter_by(id=version_id, case_id=case_id).first_or_404()

    # 创建新版本（基于旧版本内容）
    current_ver = case.current_version
    parts = current_ver.lstrip('v').split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    new_version = 'v' + '.'.join(parts)

    # 取消旧版本的最新标记
    CaseVersion.query.filter_by(case_id=case.id, is_latest=True).update({'is_latest': False})

    # 创建新版本
    version = CaseVersion(
        case_id=case.id,
        version=new_version,
        code_content=old_version.code_content,
        is_latest=True,
        created_by=current_user_id
    )
    db.session.add(version)
    case.current_version = new_version
    db.session.commit()

    return jsonify(case.to_dict(include_code=True))


@cases_bp.route('/cases/<int:case_id>/favorite', methods=['POST'])
@jwt_required()
def toggle_favorite(case_id):
    """收藏/取消收藏"""
    case = TestCase.query.get_or_404(case_id)
    case.is_favorite = not case.is_favorite
    db.session.commit()
    return jsonify({'is_favorite': case.is_favorite})


@cases_bp.route('/cases/import', methods=['POST'])
@jwt_required()
def import_cases():
    """批量导入用例"""
    current_user_id = int(get_jwt_identity())

    if 'file' not in request.files:
        return jsonify({'error': '请上传文件'}), 400

    file = request.files['file']
    module_id = request.form.get('module_id', type=int)

    if not module_id:
        return jsonify({'error': 'module_id不能为空'}), 400

    if not file.filename.endswith('.json'):
        return jsonify({'error': '只支持JSON格式'}), 400

    try:
        import json
        data = json.load(file)
        if not isinstance(data, list):
            data = [data]

        created = []
        for item in data:
            name = item.get('name', '').strip()
            if not name:
                continue

            case = TestCase(
                module_id=module_id,
                name=name,
                description=item.get('description', ''),
                tags=item.get('tags', []),
                priority=item.get('priority', 3),
                timeout=item.get('timeout', 60),
                retry=item.get('retry', 0),
                script_type=item.get('script_type', 'python'),
                current_version='v1.0.0',
                created_by=current_user_id
            )
            db.session.add(case)
            db.session.flush()

            version = CaseVersion(
                case_id=case.id,
                version='v1.0.0',
                code_content=item.get('code', ''),
                is_latest=True,
                created_by=current_user_id
            )
            db.session.add(version)
            created.append(case.id)

        db.session.commit()
        return jsonify({'message': f'成功导入{len(created)}个用例', 'ids': created}), 201

    except json.JSONDecodeError:
        return jsonify({'error': '无效的JSON格式'}), 400


@cases_bp.route('/cases/export/<int:project_id>', methods=['GET'])
@jwt_required()
def export_cases(project_id):
    """导出项目用例"""
    from app.models.module import Module

    modules = Module.query.filter_by(project_id=project_id).all()

    # 创建ZIP文件
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for module in modules:
            for case in module.cases:
                version = CaseVersion.query.filter_by(case_id=case.id, is_latest=True).first()
                if version:
                    filename = f"{module.name}/{case.name}.{case.script_type}"
                    zipf.writestr(filename, version.code_content)

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'project_{project_id}_cases.zip'
    )