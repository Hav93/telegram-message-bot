import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Input, 
  Typography,
  Tooltip,
  Avatar,
  Upload,
  message,
  Select,
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined, 
  SyncOutlined,
  ExportOutlined,
  ImportOutlined,
  UserOutlined,
  TeamOutlined,
  GlobalOutlined,
  LockOutlined,
  UnlockOutlined,
  RobotOutlined,
  UserAddOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatsApi } from '../../services/chats';
import { useCustomModal } from '../../hooks/useCustomModal';
import type { Chat } from '../../types/api';

const { Title } = Typography;
const { Search } = Input;

const ChatsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const [selectedClient, setSelectedClient] = useState<string>('all');
  const { info, Modal: CustomModalComponent } = useCustomModal();

  // 获取聊天列表
  const { data: chatsData, isLoading, refetch } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats,
  });

  // 同步聊天列表（先刷新缓存，再获取数据）
  const refreshMutation = useMutation({
    mutationFn: chatsApi.refreshChats,
    onSuccess: async (response: any) => {
      console.log('同步聊天响应:', response);
      if (response.success) {
        const count = response.count || response.updated_count || 0;
        message.success(`聊天列表同步成功，共${count}个聊天`);
        
        // 等待一小段时间确保缓存更新完成
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['chats'] });
          refetch();
        }, 500);
      } else {
        message.error(`同步失败: ${response.message || '未知错误'}`);
      }
    },
    onError: (error: any) => {
      console.error('同步聊天列表失败:', error);
      message.error(`同步失败: ${error.message || '网络错误'}`);
    },
  });

  // 导出聊天列表
  const exportMutation = useMutation({
    mutationFn: chatsApi.export,
    onSuccess: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `chats_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('聊天列表导出成功');
    },
    onError: () => {
      message.error('导出失败');
    },
  });

  // 导入聊天列表
  const importMutation = useMutation({
    mutationFn: chatsApi.import,
    onSuccess: (response: any) => {
      if (response.success) {
        message.success(response.message);
        queryClient.invalidateQueries({ queryKey: ['chats'] });
        refetch();
      } else {
        message.error(`导入失败: ${response.message}`);
      }
    },
    onError: (error: any) => {
      message.error(`导入失败: ${error.message || '网络错误'}`);
    },
  });

  const handleSearch = (value: string) => {
    setSearchText(value);
  };

  // 过滤聊天
  const filteredChats = (chatsData?.chats || []).filter((chat: Chat) => {
    // 文本搜索过滤
    const matchesSearch = chat.title?.toLowerCase().includes(searchText.toLowerCase()) ||
      chat.username?.toLowerCase().includes(searchText.toLowerCase()) ||
      chat.id.toString().includes(searchText);
    
    // 客户端过滤
    const matchesClient = selectedClient === 'all' || chat.client_id === selectedClient;
    
    return matchesSearch && matchesClient;
  });

  // 获取客户端图标
  const getClientIcon = (clientType: string) => {
    return clientType === 'bot' ? <RobotOutlined /> : <UserAddOutlined />;
  };

  // 获取客户端标签
  const getClientTag = (chat: Chat) => {
    const clientType = chat.client_type || 'user';
    const displayName = chat.client_display_name || `${clientType}: ${chat.client_id}`;
    
    return (
      <Tag 
        color={clientType === 'bot' ? 'purple' : 'cyan'} 
        icon={getClientIcon(clientType)}
      >
        {displayName}
      </Tag>
    );
  };

  const getChatTypeIcon = (type: string) => {
    switch (type) {
      case 'private':
        return <UserOutlined />;
      case 'group':
        return <TeamOutlined />;
      case 'supergroup':
        return <TeamOutlined />;
      case 'channel':
        return <GlobalOutlined />;
      default:
        return <UserOutlined />;
    }
  };

  const getChatTypeTag = (type: string) => {
    const typeMap = {
      private: { color: 'blue', text: '私聊' },
      group: { color: 'green', text: '群组' },
      supergroup: { color: 'purple', text: '超级群组' },
      channel: { color: 'orange', text: '频道' },
    };
    const config = typeMap[type as keyof typeof typeMap] || { color: 'default', text: type };
    return <Tag color={config.color} icon={getChatTypeIcon(type)}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '名称',
      key: 'name',
      width: 250,
      render: (_: any, record: Chat) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar 
            src={record.photo} 
            icon={getChatTypeIcon(record.type)}
            size="default"
            style={{ marginRight: '12px' }}
          />
          <div>
            <div style={{ fontWeight: 'bold', color: 'white', fontSize: '14px' }}>
              {record.title || record.first_name || '未知聊天'}
            </div>
            {record.username && (
              <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>
                @{record.username}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      render: (id: string) => (
        <span style={{ color: 'rgba(255,255,255,0.8)', fontFamily: 'monospace' }}>
          {id}
        </span>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      filters: [
        { text: '私聊', value: 'private' },
        { text: '群组', value: 'group' },
        { text: '超级群组', value: 'supergroup' },
        { text: '频道', value: 'channel' },
      ],
      onFilter: (value: any, record: Chat) => record.type === value,
      render: (type: string) => getChatTypeTag(type),
    },
    {
      title: '所属客户端',
      key: 'client',
      width: 200,
      filters: chatsData?.clients_info?.map((client: any) => ({
        text: client.display_name,
        value: client.client_id
      })) || [],
      onFilter: (value: any, record: Chat) => record.client_id === value,
      render: (_: any, record: Chat) => getClientTag(record),
    },
    {
      title: '成员数',
      dataIndex: 'members_count',
      key: 'members_count',
      width: 100,
      render: (count: number, record: Chat) => {
        if (record.type === 'private') return '-';
        return (
          <span style={{ color: 'rgba(255,255,255,0.8)' }}>
            {count ? count.toLocaleString() : '未知'}
          </span>
        );
      },
    },
    {
      title: '是否私密群组',
      key: 'is_private',
      width: 120,
      filters: [
        { text: '私聊', value: 'private_chat' },
        { text: '公开群组', value: 'public_group' },
        { text: '私密群组', value: 'private_group' },
        { text: '公开频道', value: 'public_channel' },
        { text: '私密频道', value: 'private_channel' },
        { text: '未知', value: 'unknown' },
      ],
      onFilter: (value: any, record: Chat) => {
        const isPrivateGroup = record.type === 'group' || record.type === 'supergroup';
        const hasInviteLink = !!record.invite_link;
        const isPublic = record.username || hasInviteLink;
        
        if (record.type === 'private') {
          return value === 'private_chat';
        } else if (record.type === 'channel') {
          return value === (isPublic ? 'public_channel' : 'private_channel');
        } else if (isPrivateGroup) {
          return value === (isPublic ? 'public_group' : 'private_group');
        }
        
        return value === 'unknown';
      },
      render: (_: any, record: Chat) => {
        // 判断是否为私密群组
        const isPrivateGroup = record.type === 'group' || record.type === 'supergroup';
        const hasInviteLink = !!record.invite_link;
        const isPublic = record.username || hasInviteLink;
        
        if (record.type === 'private') {
          return <Tag color="blue" icon={<LockOutlined />}>私聊</Tag>;
        } else if (record.type === 'channel') {
          return isPublic ? 
            <Tag color="green" icon={<UnlockOutlined />}>公开频道</Tag> : 
            <Tag color="orange" icon={<LockOutlined />}>私密频道</Tag>;
        } else if (isPrivateGroup) {
          return isPublic ? 
            <Tag color="green" icon={<UnlockOutlined />}>公开群组</Tag> : 
            <Tag color="red" icon={<LockOutlined />}>私密群组</Tag>;
        }
        
        return <Tag color="default">未知</Tag>;
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Chat) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="primary"
              size="small"
              onClick={() => {
                const chatTypeText = record.type === 'private' ? '私聊' :
                                   record.type === 'group' ? '群组' :
                                   record.type === 'supergroup' ? '超级群组' :
                                   record.type === 'channel' ? '频道' : record.type;
                
                const isPrivateGroup = record.type === 'group' || record.type === 'supergroup';
                const hasInviteLink = !!record.invite_link;
                const isPublic = record.username || hasInviteLink;
                let privacyStatus = '';
                
                if (record.type === 'private') {
                  privacyStatus = '私聊';
                } else if (record.type === 'channel') {
                  privacyStatus = isPublic ? '公开频道' : '私密频道';
                } else if (isPrivateGroup) {
                  privacyStatus = isPublic ? '公开群组' : '私密群组';
                }
                
                const chatDetails = `聊天名称: ${record.title || record.first_name || '未知聊天'}${record.username ? `\n用户名: @${record.username}` : ''}\nID: ${record.id}\n类型: ${chatTypeText}\n隐私状态: ${privacyStatus}${record.description ? `\n描述: ${record.description}` : ''}${record.type !== 'private' && record.members_count ? `\n成员数: ${record.members_count.toLocaleString()}` : ''}\n状态: ${record.is_active !== false ? '活跃' : '非活跃'}\n最后活动: ${record.last_activity ? new Date(record.last_activity).toLocaleString() : '未知'}${record.invite_link ? `\n邀请链接: ${record.invite_link}` : ''}`;
                
                info({
                  title: '聊天详情',
                  content: chatDetails,
                  confirmText: '我知道了',
                });
              }}
            >
              详情
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ margin: 0, color: 'white' }}>聊天管理</Title>
          <Space>
            <Select
              value={selectedClient}
              onChange={setSelectedClient}
              style={{ width: 200 }}
              placeholder="选择客户端"
            >
              <Select.Option value="all">全部客户端</Select.Option>
              {chatsData?.clients_info?.map((client: any) => (
                <Select.Option key={client.client_id} value={client.client_id}>
                  {getClientIcon(client.client_type)} {client.display_name} ({client.chat_count})
                </Select.Option>
              ))}
            </Select>
            <Search
              placeholder="搜索聊天..."
              allowClear
              style={{ width: 250 }}
              onChange={(e) => handleSearch(e.target.value)}
              prefix={<SearchOutlined />}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                console.log('手动刷新聊天列表');
                refetch();
              }}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={() => refreshMutation.mutate()}
              loading={refreshMutation.isPending}
            >
              同步聊天
            </Button>
          </Space>
        </div>

        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            <span style={{ color: 'rgba(255,255,255,0.8)' }}>
              共找到 {filteredChats.length} 个聊天
            </span>
            {chatsData?.last_updated && (
              <span style={{ color: 'rgba(255,255,255,0.6)' }}>
                最后更新: {new Date(chatsData.last_updated).toLocaleString()}
              </span>
            )}
          </Space>
          <Space>
            <Upload
              accept=".json"
              showUploadList={false}
              beforeUpload={(file) => {
                const formData = new FormData();
                formData.append('file', file);
                importMutation.mutate(formData);
                return false;
              }}
            >
              <Button
                icon={<ImportOutlined />}
                loading={importMutation.isPending}
              >
                导入
              </Button>
            </Upload>
            <Button
              icon={<ExportOutlined />}
              onClick={() => exportMutation.mutate()}
              loading={exportMutation.isPending}
            >
              导出
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={filteredChats}
          rowKey="id"
          loading={isLoading}
          locale={{
            emptyText: (
              <div style={{ 
                padding: '40px 20px',
                textAlign: 'center',
                color: 'rgba(255, 255, 255, 0.6)',
                background: 'rgba(255, 255, 255, 0.03)',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(8px)',
                margin: '20px 0',
                textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>💬</div>
                <div style={{ fontSize: '16px', marginBottom: '8px' }}>暂无聊天数据</div>
                <div style={{ fontSize: '14px' }}>点击"同步聊天"获取Telegram聊天列表</div>
              </div>
            )
          }}
          pagination={{
            total: filteredChats.length,
            pageSize: 15,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个聊天`,
          }}
          style={{ 
            background: 'transparent',
          }}
        />
      </Card>
      
      {/* 自定义Modal */}
      {CustomModalComponent}
    </div>
  );
};

export default ChatsPage;
