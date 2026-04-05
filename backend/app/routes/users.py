from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.audit import AuditLog

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    keyword = request.args.get('keyword', '')

    query = User.query

    if keyword:
        query = query.filter(User.username.contains(keyword))

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })


@users_bp.route('', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if not password:
        return jsonify({'error': '密码不能为空'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户已存在'}), 400

    user = User(username=username)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='create',
        resource_type='user',
        resource_id=user.id,
        details={'username': username},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取用户详情"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户"""
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    user = User.query.get_or_404(user_id)

    # 更新密码
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    db.session.commit()

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='update',
        resource_type='user',
        resource_id=user.id,
        details={'updated_fields': list(data.keys())},
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(user.to_dict())


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    current_user_id = int(get_jwt_identity())

    user = User.query.get_or_404(user_id)

    # 审计日志
    log = AuditLog(
        user_id=current_user_id,
        action='delete',
        resource_type='user',
        resource_id=user.id,
        details={'username': user.username},
        ip_address=request.remote_addr
    )
    db.session.add(log)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': '删除成功'})