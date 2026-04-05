import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app('app.config.TestConfig')
    with app.app_context():
        db.create_all()

        # 创建测试用户
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        tester = User(username='tester1')
        tester.set_password('test123')
        db.session.add(tester)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_token(client, app):
    """获取认证token"""
    with app.app_context():
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        return response.json.get('access_token')


@pytest.fixture
def auth_headers(auth_token):
    """获取认证头"""
    return {'Authorization': f'Bearer {auth_token}'}