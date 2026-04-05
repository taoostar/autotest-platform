from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.audit import AuditLog

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username:
        return jsonify({'error': '请输入用户名'}), 400
    if not password:
        return jsonify({'error': '请输入密码'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401

    # 创建不过期的token
    access_token = create_access_token(identity=str(user.id))

    # 设置cookie
    response = jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'access_token': access_token
    })
    response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')

    # 审计日志
    log = AuditLog(
        user_id=user.id,
        action='login',
        resource_type='auth',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    return response


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    user_id = int(get_jwt_identity())

    # 审计日志
    log = AuditLog(
        user_id=user_id,
        action='logout',
        resource_type='auth',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    response = jsonify({'message': '登出成功'})
    response.delete_cookie('access_token')
    return response


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': '用户不存在'}), 404

    return jsonify(user.to_dict())