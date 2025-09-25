import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const LoginPage: React.FC = () => {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%)'
    }}>
      <Card className="glass-card" style={{ width: 400 }}>
        <Title level={2} style={{ textAlign: 'center' }}>登录</Title>
        <p style={{ textAlign: 'center' }}>登录功能正在开发中...</p>
      </Card>
    </div>
  );
};

export default LoginPage;
