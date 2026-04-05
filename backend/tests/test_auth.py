import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app('app.config.TestConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    """测试健康检查接口"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'


def test_register_and_login(client, app):
    """测试用户注册和登录"""
    # 注册
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    # 注意：这个会失败，因为我们用的是login接口创建用户
    # 先创建用户
    with app.app_context():
        user = User(username='testuser')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

    # 登录
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json


def test_login_invalid_credentials(client):
    """测试无效凭据登录"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpass'
    })
    assert response.status_code == 401


def test_login_empty_username(client):
    """测试空用户名登录"""
    response = client.post('/api/v1/auth/login', json={
        'username': '',
        'password': 'testpass'
    })
    assert response.status_code == 400


def test_login_empty_password(client):
    """测试空密码登录"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': ''
    })
    assert response.status_code == 400