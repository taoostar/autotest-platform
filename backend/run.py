#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db, socketio
from app.models import *

from app.config import Config
app = create_app(Config)


def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("数据库表创建成功")

        # 创建默认管理员账号
        from app.models.user import User
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("默认管理员账号创建成功: admin/admin123")
        else:
            print("管理员账号已存在")


if __name__ == '__main__':
    # 初始化数据库
    init_db()

    # 启动服务
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)