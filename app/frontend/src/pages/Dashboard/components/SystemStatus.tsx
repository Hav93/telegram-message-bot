import React from 'react';
import { Card, Badge, Space, Typography, Divider, Button, Skeleton } from 'antd';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { SystemStatus as SystemStatusType } from '../../../types/api';

const { Text } = Typography;

interface SystemStatusProps {
  status?: SystemStatusType;
  loading?: boolean;
}

const SystemStatus: React.FC<SystemStatusProps> = ({ status, loading = false }) => {
  if (loading) {
    return (
      <Card title="系统状态" className="glass-card" style={{ height: 400 }}>
        <Skeleton active paragraph={{ rows: 6 }} />
      </Card>
    );
  }

  const getStatusBadge = (connected: boolean) => {
    return connected ? (
      <Badge status="success" text="已连接" />
    ) : (
      <Badge status="error" text="未连接" />
    );
  };

  // const getWebStatusBadge = (webStatus: string) => {
  //   const statusMap = {
  //     running: { status: 'success' as const, text: '运行中' },
  //     stopped: { status: 'default' as const, text: '已停止' },
  //     error: { status: 'error' as const, text: '错误' },
  //   };
  //   
  //   const config = statusMap[webStatus as keyof typeof statusMap] || statusMap.error;
  //   return <Badge status={config.status} text={config.text} />;
  // };

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          系统状态
        </Space>
      }
      className="glass-card"
      style={{ height: 400 }}
      extra={
        <Button
          type="text"
          icon={<ReloadOutlined />}
          size="small"
        />
      }
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Telegram连接状态 */}
        <div>
          <Space align="center" style={{ marginBottom: 8 }}>
            {status?.logged_in ? (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
            ) : (
              <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />
            )}
            <Text strong>Telegram连接</Text>
          </Space>
          {getStatusBadge(status?.logged_in || false)}
        </div>

        {/* 用户信息 */}
        {status?.user && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>用户信息</Text>
              <Space direction="vertical" size="small">
                <Text type="secondary">
                  姓名: <Text strong>{status.user.first_name} {status.user.last_name || ''}</Text>
                </Text>
                {status.user.username && (
                  <Text type="secondary">
                    用户名: <Text strong>@{status.user.username}</Text>
                  </Text>
                )}
                {status.user.phone && (
                  <Text type="secondary">
                    手机号: <Text strong>{status.user.phone}</Text>
                  </Text>
                )}
              </Space>
            </div>
          </>
        )}

        {/* 错误信息 */}
        {status?.error && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <div>
              <Text type="danger" style={{ fontSize: '12px' }}>
                <ExclamationCircleOutlined style={{ marginRight: 4 }} />
                {status.error}
              </Text>
            </div>
          </>
        )}
      </Space>
    </Card>
  );
};

export default SystemStatus;
