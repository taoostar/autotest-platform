import { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Drawer } from 'antd';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  HomeOutlined,
  FolderOutlined,
  PlayCircleOutlined,
  RobotOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/cases', icon: <FolderOutlined />, label: '测试用例' },
  { key: '/plans', icon: <PlayCircleOutlined />, label: '测试计划' },
  { key: '/tasks', icon: <ClockCircleOutlined />, label: '测试任务' },
  { key: '/agents', icon: <RobotOutlined />, label: 'Agent管理' },
  { key: '/reports', icon: <BarChartOutlined />, label: '报告中心' },
  { key: '/schedules', icon: <ClockCircleOutlined />, label: '定时任务' },
  { key: '/webhooks', icon: <ThunderboltOutlined />, label: 'Webhook' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleMenuClick = ({ key }) => {
    navigate(key);
    setMobileMenuOpen(false);
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.username || '用户',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 移动端侧边栏 - 使用 Drawer */}
      <Drawer
        title="AutoTest"
        placement="left"
        onClose={() => setMobileMenuOpen(false)}
        open={mobileMenuOpen}
        width={200}
        styles={{ body: { padding: 0 } }}
      >
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Drawer>

      {/* 桌面端侧边栏 */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          overflow: 'auto',
          zIndex: 10,
        }}
        breakpoint="lg"
        collapsedWidth={80}
        onBreakpoint={(broken) => {
          if (broken) {
            setCollapsed(true);
          }
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 14 : 18,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? 'AT' : 'AutoTest'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }} className="main-layout-content">
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          }}
        >
          <Button
            icon={<MenuOutlined />}
            onClick={() => setMobileMenuOpen(true)}
            className="mobile-menu-btn"
            style={{ display: 'none' }}
          />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
          </Dropdown>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}