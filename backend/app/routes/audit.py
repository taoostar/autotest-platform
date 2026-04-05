from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.audit import AuditLog

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('', methods=['GET'])
@jwt_required()
def list_audit_logs():
    """获取审计日志列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action', '')
    resource_type = request.args.get('resource_type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = AuditLog.query

    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter_by(action=action)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size
    })