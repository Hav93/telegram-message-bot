import React from 'react';
import { Card, Table, Tag, Space, Typography, Button } from 'antd';
import { FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import type { MessageLog } from '../../../types/rule.ts';

const { Text } = Typography;

interface RecentLogsProps {
  logs: MessageLog[];
  loading?: boolean;
}

const RecentLogs: React.FC<RecentLogsProps> = ({ logs, loading = false }) => {
  const navigate = useNavigate();

  const getStatusTag = (status: string) => {
    const statusConfig = {
      success: { color: 'success', text: '成功' },
      failed: { color: 'error', text: '失败' },
      filtered: { color: 'warning', text: '已过滤' },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.failed;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getMessageTypeTag = (type: string) => {
    const typeConfig = {
      text: { color: 'blue', text: '文本' },
      photo: { color: 'green', text: '图片' },
      video: { color: 'purple', text: '视频' },
      document: { color: 'orange', text: '文档' },
      audio: { color: 'cyan', text: '音频' },
      voice: { color: 'magenta', text: '语音' },
      sticker: { color: 'gold', text: '贴纸' },
      animation: { color: 'lime', text: '动图' },
    };
    
    const config = typeConfig[type as keyof typeof typeConfig] || { color: 'default', text: type };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (time: string) => (
        <Text style={{ fontSize: 12 }}>
          {dayjs(time).format('MM-DD HH:mm')}
        </Text>
      ),
    },
    {
      title: '规则',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 120,
      render: (name: string) => (
        <Text ellipsis style={{ maxWidth: 100 }}>
          {name || '未知规则'}
        </Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'message_type',
      key: 'message_type',
      width: 80,
      render: (type: string) => getMessageTypeTag(type),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '内容',
      dataIndex: 'message_text',
      key: 'message_text',
      ellipsis: true,
      render: (text: string) => (
        <Text
          style={{ fontSize: 12 }}
          ellipsis={{ tooltip: text }}
        >
          {text || '非文本消息'}
        </Text>
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          最近日志
        </Space>
      }
      className="glass-card"
      extra={
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate('/logs')}
        >
          查看全部
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={logs}
        loading={loading}
        pagination={false}
        size="small"
        rowKey="id"
        locale={{
          emptyText: '暂无日志记录',
        }}
        scroll={{ y: 300 }}
      />
    </Card>
  );
};

export default RecentLogs;
