import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic,
  Switch
} from 'antd';
import {
  PlayCircleOutlined,
  StopOutlined,
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  UserOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoginOutlined,
  PoweroffOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { ClientLoginModal } from './ClientLoginModal';

const { Title, Text } = Typography;
const { Option } = Select;

interface ClientInfo {
  client_id: string;
  client_type: 'user' | 'bot';
  running: boolean;
  connected: boolean;
  user_info?: {
    id: number;
    username: string;
    first_name: string;
    phone: string;
  };
  monitored_chats: number[];
  thread_alive: boolean;
  auto_start?: boolean;
}

interface SystemStatus {
  success: boolean;
  enhanced_mode: boolean;
  clients: Record<string, ClientInfo>;
  total_clients: number;
  running_clients: number;
  connected_clients: number;
}

const ClientManagement: React.FC = () => {
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState<string>('');
  const [selectedClientType, setSelectedClientType] = useState<'user' | 'bot'>('user');
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取客户端列表
  const { data: clientsData, isLoading, refetch } = useQuery<{
    success: boolean;
    clients: Record<string, ClientInfo>;
  }>({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await axios.get('/api/clients');
      return response.data;
    },
    refetchInterval: 5000, // 5秒刷新一次
  });

  // 获取系统状态
  const { data: systemStatus } = useQuery<SystemStatus>({
    queryKey: ['system-enhanced-status'],
    queryFn: async () => {
      const response = await axios.get('/api/system/enhanced-status');
      return response.data;
    },
    refetchInterval: 5000,
  });

  // 启动客户端
  const startClientMutation = useMutation({
    mutationFn: async (clientId: string) => {
      const response = await axios.post(`/api/clients/${clientId}/start`);
      return response.data;
    },
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '启动失败');
    },
  });

  // 停止客户端
  const stopClientMutation = useMutation({
    mutationFn: async (clientId: string) => {
      const response = await axios.post(`/api/clients/${clientId}/stop`);
      return response.data;
    },
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '停止失败');
    },
  });

  // 添加客户端
  const addClientMutation = useMutation({
    mutationFn: async (values: any) => {
      const response = await axios.post('/api/clients', values);
      return response.data;
    },
    onSuccess: (data) => {
      console.log('🎯 添加客户端API响应:', data);
      if (data.success) {
        message.success(data.message);
        setAddModalVisible(false);
        form.resetFields();
        queryClient.invalidateQueries({ queryKey: ['clients'] });
        
        // 如果是用户客户端且需要验证，自动打开登录模态框
        console.log('🔍 检查验证需求:', { need_verification: data.need_verification, client_id: data.client_id });
        if (data.need_verification && data.client_id) {
          console.log('✅ 自动打开登录模态框');
          setSelectedClientId(data.client_id);
          setSelectedClientType('user');
          setLoginModalVisible(true);
        } else {
          console.log('❌ 不需要验证或缺少client_id');
        }
      } else {
        message.error(data.message);
      }
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '添加失败');
    },
  });

  // 删除客户端
  const removeClientMutation = useMutation({
    mutationFn: async (clientId: string) => {
      const response = await axios.delete(`/api/clients/${clientId}`);
      return response.data;
    },
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 切换自动启动
  const toggleAutoStartMutation = useMutation({
    mutationFn: async ({ clientId, autoStart }: { clientId: string; autoStart: boolean }) => {
      const response = await axios.post(`/api/clients/${clientId}/auto-start`, {
        auto_start: autoStart
      });
      return response.data;
    },
    onSuccess: (data) => {
      message.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '设置失败');
    },
  });

  const handleAddClient = () => {
    form.validateFields().then(values => {
      addClientMutation.mutate(values);
    });
  };

  const handleShowLogin = (clientId: string, clientType: 'user' | 'bot') => {
    if (clientType !== 'user') {
      message.info('只有用户客户端支持验证码登录');
      return;
    }
    setSelectedClientId(clientId);
    setSelectedClientType(clientType);
    setLoginModalVisible(true);
  };

  const handleLoginSuccess = () => {
    setLoginModalVisible(false);
    queryClient.invalidateQueries({ queryKey: ['clients'] });
    message.success('用户客户端登录成功！');
  };

  const getStatusTag = (client: ClientInfo) => {
    if (!client.running) {
      return <Tag color="default">已停止</Tag>;
    }
    if (client.connected) {
      return <Tag color="success" icon={<CheckCircleOutlined />}>已连接</Tag>;
    }
    return <Tag color="processing">连接中</Tag>;
  };

  const getClientTypeIcon = (type: string) => {
    return type === 'bot' ? <RobotOutlined /> : <UserOutlined />;
  };

  const columns = [
    {
      title: '客户端ID',
      dataIndex: 'client_id',
      key: 'client_id',
      render: (text: string, record: ClientInfo) => (
        <Space>
          {getClientTypeIcon(record.client_type)}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'client_type',
      key: 'client_type',
      render: (type: string) => (
        <Tag color={type === 'bot' ? 'blue' : 'green'}>
          {type === 'bot' ? '机器人' : '用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (record: ClientInfo) => getStatusTag(record),
    },
    {
      title: '用户信息',
      key: 'user_info',
      render: (record: ClientInfo) => {
        if (!record.user_info) {
          return <Text type="secondary">未获取</Text>;
        }
        return (
          <div>
            <div>{record.user_info.first_name}</div>
            {record.user_info.username && (
              <Text type="secondary">@{record.user_info.username}</Text>
            )}
            {record.user_info.phone && (
              <Text type="secondary">{record.user_info.phone}</Text>
            )}
          </div>
        );
      },
    },
    {
      title: '监听聊天',
      dataIndex: 'monitored_chats',
      key: 'monitored_chats',
      render: (chats: number[]) => (
        <Text>{chats?.length || 0} 个</Text>
      ),
    },
    {
      title: '线程状态',
      dataIndex: 'thread_alive',
      key: 'thread_alive',
      render: (alive: boolean) => (
        <Tag color={alive ? 'success' : 'error'}>
          {alive ? '活跃' : '停止'}
        </Tag>
      ),
    },
    {
      title: '自动启动',
      key: 'auto_start',
      render: (record: ClientInfo) => (
        <Switch
          checked={record.auto_start || false}
          onChange={(checked) => {
            toggleAutoStartMutation.mutate({
              clientId: record.client_id,
              autoStart: checked
            });
          }}
          checkedChildren={<PoweroffOutlined />}
          unCheckedChildren={<PoweroffOutlined />}
          loading={toggleAutoStartMutation.isPending}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: ClientInfo) => (
        <Space>
          {!record.running ? (
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => startClientMutation.mutate(record.client_id)}
              loading={startClientMutation.isPending}
            >
              启动
            </Button>
          ) : (
            <Button
              size="small"
              icon={<StopOutlined />}
              onClick={() => stopClientMutation.mutate(record.client_id)}
              loading={stopClientMutation.isPending}
            >
              停止
            </Button>
          )}
          
          {/* 用户客户端登录按钮 */}
          {record.client_type === 'user' && !record.connected && (
            <Button
              size="small"
              icon={<LoginOutlined />}
              onClick={() => handleShowLogin(record.client_id, record.client_type)}
              title="验证码登录"
            >
              登录
            </Button>
          )}
          
          <Popconfirm
            title="确定要删除这个客户端吗？"
            onConfirm={() => removeClientMutation.mutate(record.client_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              loading={removeClientMutation.isPending}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const clients = clientsData?.clients ? Object.values(clientsData.clients) : [];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>客户端管理</Title>
        <Text type="secondary">
          管理Telegram客户端实例，支持多用户和机器人客户端并发运行
        </Text>
      </div>

      {/* 统计信息 */}
      {systemStatus?.enhanced_mode && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总客户端数"
                value={systemStatus.total_clients || 0}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中"
                value={systemStatus.running_clients || 0}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已连接"
                value={systemStatus.connected_clients || 0}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="增强模式"
                value={systemStatus.enhanced_mode ? "启用" : "禁用"}
                prefix={<RobotOutlined />}
                valueStyle={{ 
                  color: systemStatus.enhanced_mode ? '#3f8600' : '#cf1322' 
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {!systemStatus?.enhanced_mode && (
        <Card style={{ marginBottom: '24px' }}>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <CloseCircleOutlined style={{ fontSize: '48px', color: '#faad14', marginBottom: '16px' }} />
            <Title level={4}>传统模式运行中</Title>
            <Text type="secondary">
              当前运行在传统模式，客户端管理功能不可用。
              请使用增强版启动器 (web_enhanced.py) 来启用多客户端管理功能。
            </Text>
          </div>
        </Card>
      )}

      {/* 客户端列表 */}
      <Card
        title="客户端列表"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAddModalVisible(true)}
              disabled={!systemStatus?.enhanced_mode}
            >
              添加客户端
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={clients}
          rowKey="client_id"
          loading={isLoading}
          pagination={false}
          locale={{
            emptyText: systemStatus?.enhanced_mode 
              ? '暂无客户端，点击"添加客户端"开始'
              : '增强模式未启用'
          }}
        />
      </Card>

      {/* 添加客户端模态框 */}
      <Modal
        title="添加客户端"
        open={addModalVisible}
        onOk={handleAddClient}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={addClientMutation.isPending}
        zIndex={1050}
        getContainer={false}
      >
        <Form 
          form={form} 
          layout="vertical"
          onValuesChange={(changedValues) => {
            if (changedValues.client_type) {
              // 当客户端类型改变时，重置表单相关字段
              if (changedValues.client_type === 'bot') {
                form.setFieldsValue({
                  api_id: undefined,
                  api_hash: undefined,
                  phone: undefined
                });
              } else {
                form.setFieldsValue({
                  bot_token: undefined,
                  admin_user_id: undefined
                });
              }
            }
          }}
        >
          <Form.Item
            name="client_id"
            label="客户端ID"
            rules={[{ required: true, message: '请输入客户端ID' }]}
          >
            <Input placeholder="例如: user1, bot1, main_user2" />
          </Form.Item>
          
          <Form.Item
            name="client_type"
            label="客户端类型"
            rules={[{ required: true, message: '请选择客户端类型' }]}
            initialValue="user"
          >
            <Select
              placeholder="选择客户端类型"
              dropdownStyle={{ zIndex: 1051 }}
              getPopupContainer={(triggerNode) => triggerNode.parentNode as HTMLElement}
            >
              <Option value="user">用户客户端</Option>
              <Option value="bot">机器人客户端</Option>
            </Select>
          </Form.Item>

          {/* 机器人客户端专用字段 */}
          <Form.Item shouldUpdate={(prevValues, curValues) => prevValues.client_type !== curValues.client_type}>
            {({ getFieldValue }) => {
              const clientType = getFieldValue('client_type');
              if (clientType === 'bot') {
                return (
                  <>
                    <Form.Item
                      name="bot_token"
                      label="Bot Token"
                      rules={[{ required: true, message: '请输入Bot Token' }]}
                      tooltip="从 @BotFather 获得的Bot Token"
                    >
                      <Input.Password placeholder="例如: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz" />
                    </Form.Item>
                    
                    <Form.Item
                      name="admin_user_id"
                      label="管理员用户ID"
                      rules={[{ required: true, message: '请输入管理员用户ID' }]}
                      tooltip="有权管理此机器人的用户ID，可以从 @userinfobot 获取"
                    >
                      <Input placeholder="例如: 123456789" />
                    </Form.Item>
                  </>
                );
              }
              return null;
            }}
          </Form.Item>

          {/* 用户客户端专用字段 */}
          <Form.Item shouldUpdate={(prevValues, curValues) => prevValues.client_type !== curValues.client_type}>
            {({ getFieldValue }) => {
              const clientType = getFieldValue('client_type');
              if (clientType === 'user') {
                return (
                  <>
                    <Form.Item
                      name="api_id"
                      label="API ID"
                      rules={[{ required: true, message: '请输入API ID' }]}
                      tooltip="从 https://my.telegram.org 获得的API ID"
                    >
                      <Input placeholder="例如: 1234567" />
                    </Form.Item>
                    
                    <Form.Item
                      name="api_hash"
                      label="API Hash"
                      rules={[{ required: true, message: '请输入API Hash' }]}
                      tooltip="从 https://my.telegram.org 获得的API Hash"
                    >
                      <Input.Password placeholder="例如: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" />
                    </Form.Item>
                    
                    <Form.Item
                      name="phone"
                      label="手机号"
                      rules={[
                        { required: true, message: '请输入手机号' },
                        { pattern: /^\+?\d{10,15}$/, message: '请输入有效的手机号' }
                      ]}
                      tooltip="包含国际区号的手机号，例如: +8613812345678"
                    >
                      <Input placeholder="例如: +8613812345678" />
                    </Form.Item>
                  </>
                );
              }
              return null;
            }}
          </Form.Item>
        </Form>
      </Modal>

      {/* 用户客户端登录模态框 */}
      <ClientLoginModal
        visible={loginModalVisible}
        onCancel={() => setLoginModalVisible(false)}
        onSuccess={handleLoginSuccess}
        clientId={selectedClientId}
        clientType={selectedClientType}
      />
    </div>
  );
};

export default ClientManagement;
