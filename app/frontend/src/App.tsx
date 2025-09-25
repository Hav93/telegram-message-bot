import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Layout
import MainLayout from './components/common/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import RulesPage from './pages/Rules';
import LogsPage from './pages/Logs';
import SettingsPage from './pages/Settings';
import ChatsPage from './pages/Chats';
import ClientManagement from './pages/ClientManagement';
import LoginPage from './pages/Login';

// Styles
import './App.css';

// 创建React Query客户端 - 修复缓存同步
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 0, // 立即过期，确保数据新鲜
      gcTime: 5 * 60 * 1000, // 5分钟垃圾回收
      refetchOnMount: true, // 组件挂载时总是重新获取
      refetchOnWindowFocus: true, // 窗口聚焦时重新获取
      refetchOnReconnect: true, // 网络重连时重新获取
    },
    mutations: {
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={zhCN}>
        <AntApp>
          <Router>
            <div className="main-layout">
              <Routes>
                {/* 登录页面 */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* 主应用路由 */}
                <Route path="/" element={<MainLayout />}>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={<Dashboard />} />
                  <Route path="rules/*" element={<RulesPage />} />
                  <Route path="logs" element={<LogsPage />} />
                  <Route path="chats" element={<ChatsPage />} />
                  <Route path="clients" element={<ClientManagement />} />
                  <Route path="settings" element={<SettingsPage />} />
                </Route>
                
                {/* 404重定向 */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </Router>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
};

export default App;