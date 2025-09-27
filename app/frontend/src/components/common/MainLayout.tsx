import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Typography,
  Space,
} from 'antd';
import { useQuery } from '@tanstack/react-query';
import {
  DashboardOutlined,
  SettingOutlined,
  FileTextOutlined,
  MessageOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
} from '@ant-design/icons';
import ThemeSwitcher from '../ThemeSwitcher';

const { Header, Sider } = Layout;
const { Text } = Typography;

// 菜单项配置
const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表板',
    path: '/dashboard',
    title: '📊 仪表板',
    description: '系统运行状态和数据统计概览',
  },
  {
    key: '/rules',
    icon: <SettingOutlined />,
    label: '转发规则',
    path: '/rules',
    title: '⚙️ 转发规则',
    description: '配置和管理消息转发规则',
  },
  {
    key: '/logs',
    icon: <FileTextOutlined />,
    label: '消息日志',
    path: '/logs',
    title: '📝 消息日志',
    description: '查看消息转发历史记录',
  },
  {
    key: '/chats',
    icon: <MessageOutlined />,
    label: '聊天管理',
    path: '/chats',
    title: '💬 聊天管理',
    description: '管理群组和频道信息',
  },
  {
    key: '/clients',
    icon: <TeamOutlined />,
    label: '客户端管理',
    path: '/clients',
    title: '🤖 客户端管理',
    description: '管理Telegram客户端实例',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
    path: '/settings',
    title: '🔧 系统设置',
    description: '配置系统参数和Bot设置',
  },
];

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 获取系统信息
  const { data: systemInfo } = useQuery({
    queryKey: ['systemInfo'],
    queryFn: async () => {
      const response = await fetch('/api/system/enhanced-status');
      return response.json();
    },
    refetchInterval: 30000, // 每30秒刷新一次
  });

  // 菜单点击处理
  const handleMenuClick = (key: string) => {
    const item = menuItems.find(item => item.key === key);
    if (item) {
      navigate(item.path);
    }
  };

  // 获取当前选中的菜单
  const getSelectedKeys = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if (path.startsWith(item.key)) {
        return [item.key];
      }
    }
    return ['/dashboard'];
  };

  // 获取当前页面信息
  const getCurrentPageInfo = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if (path.startsWith(item.key)) {
        return { title: item.title, description: item.description };
      }
    }
    return { title: '📊 仪表板', description: '系统运行状态和数据统计概览' };
  };

  const currentPageInfo = getCurrentPageInfo();

  return (
    <div className="main-layout-wrapper" style={{ height: '100vh', overflow: 'hidden' }}>
      {/* 固定的侧边栏 */}
      <Sider
        className="fixed-sidebar"
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        width={240}
        collapsedWidth={80}
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          height: '100vh',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Logo区域 (Telegram Message 🚀 v2.0) */}
        <div
          style={{
            minHeight: sidebarCollapsed ? 64 : 88,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: sidebarCollapsed ? '16px 8px' : '16px 24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.2)',
            gap: 4,
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: sidebarCollapsed ? 0 : 12,
          }}>
            <MessageOutlined
              style={{
                fontSize: 24,
                color: '#ffffff',
                textShadow: '0 1px 3px rgba(0, 0, 0, 0.5)',
              }}
            />
            {!sidebarCollapsed && (
              <Text strong style={{ 
                fontSize: 16, 
                color: '#ffffff',
                textShadow: '0 1px 3px rgba(0, 0, 0, 0.5)',
                fontWeight: 600,
              }}>
                Telegram Message
              </Text>
            )}
          </div>
          
          <div style={{ 
            fontSize: sidebarCollapsed ? 10 : 11, 
            opacity: 0.9, 
            color: '#ffffff',
            textAlign: 'center',
            fontWeight: 500,
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
          }}>
            🚀 v{systemInfo?.app_version || '3.8.0'}
          </div>
        </div>

        {/* 菜单区域 - 占用剩余空间 */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Menu
            mode="inline"
            selectedKeys={getSelectedKeys()}
            style={{
              border: 'none',
              background: 'transparent',
              height: '100%',
            }}
            items={menuItems.map(item => ({
              key: item.key,
              icon: item.icon,
              label: item.label,
              onClick: () => handleMenuClick(item.key),
            }))}
          />
        </div>

        {/* 折叠/展开按钮 - 绝对底部位置 */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            padding: '16px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <Button
            type="text"
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              fontSize: 16,
              width: 40,
              height: 40,
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '8px',
              transition: 'all 0.3s ease',
              background: 'rgba(255, 255, 255, 0.1)',
            }}
          />
        </div>
      </Sider>

      {/* 右侧主区域：header + content */}
      <div
        style={{
          marginLeft: sidebarCollapsed ? 80 : 240,
          width: `calc(100vw - ${sidebarCollapsed ? 80 : 240}px)`,
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          transition: 'margin-left 0.3s ease, width 0.3s ease',
        }}
      >
        {/* 顶部导航栏 - 不再fixed，在正常文档流中 */}
        <Header 
          className="layout-header"
          style={{
            height: 64,
            flexShrink: 0,
            zIndex: 11,
            padding: 0,
          }}
        >
          <div className="header-content" style={{ padding: '0 32px' }}>
            {/* 左侧：页面信息（占更多空间） */}
            <div style={{ flex: 1, maxWidth: 'calc(100% - 200px)' }}>
              <Text className="header-title" style={{ 
                color: 'white', 
                fontSize: 20, 
                fontWeight: 600,
                display: 'block',
                lineHeight: 1.2,
              }}>
                {currentPageInfo.title}
              </Text>
              <div style={{ 
                fontSize: 13, 
                opacity: 0.85, 
                color: 'rgba(255, 255, 255, 0.85)',
                marginTop: 2,
                lineHeight: 1.3,
              }}>
                {currentPageInfo.description}
              </div>
            </div>

            {/* 右侧：主题切换器和用户信息 */}
            <Space align="center" size={16}>
              <ThemeSwitcher />
              <Avatar
                size={40}
                icon={<UserOutlined />}
                style={{ backgroundColor: '#667eea', fontSize: 18 }}
              />
              <div className="user-info">
                <Text style={{ color: 'white', fontSize: 16, fontWeight: 500 }}>用户</Text>
              </div>
            </Space>
          </div>
        </Header>

        {/* 主内容区域 - 自然在header下方，可以滚动 */}
        <div
          className="main-content-area"
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px',
            background: 'transparent',
          }}
        >
          <div className="fade-in">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainLayout;