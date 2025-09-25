import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Input, 
  DatePicker, 
  Select,
  Typography,
  Tooltip,
  Upload,
  message
} from 'antd';
import { 
  SearchOutlined, 
  ReloadOutlined, 
  ExportOutlined, 
  ImportOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { logsApi } from '../../services/logs';
import { chatsApi } from '../../services/chats';
import { useCustomModal } from '../../hooks/useCustomModal';
import type { MessageLog, LogFilters } from '../../types/rule';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Search } = Input;
const { RangePicker } = DatePicker;
const { Option } = Select;

const LogsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { confirm, info, Modal: CustomModalComponent } = useCustomModal();
  const [filters, setFilters] = useState<LogFilters>({
    page: 1,
    limit: 20,
  });
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 获取日志列表
  const { data: logsData, isLoading, refetch } = useQuery({
    queryKey: ['logs', filters],
    queryFn: () => logsApi.list(filters),
  });

  // 获取聊天列表
  const { data: chatsData } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats
  });

  const chats = chatsData?.chats || [];

  // 根据chat_id获取聊天显示名称（优先first_name）
  const getChatDisplayName = (chatId: string) => {
    const chat = chats.find(chat => String(chat.id) === String(chatId));
    if (chat) {
      return chat.title || chat.id;
    }
    return `聊天 ${chatId}`;
  };

  // 批量删除日志
  const batchDeleteMutation = useMutation({
    mutationFn: logsApi.batchDelete,
    onSuccess: () => {
      message.success('日志删除成功');
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['logs'] });
      refetch();
    },
    onError: (error: any) => {
      console.error('批量删除日志失败:', error);
      message.error(`删除失败: ${error.message || '网络错误'}`);
    },
  });

  // 导出日志
  const exportMutation = useMutation({
    mutationFn: logsApi.export,
    onSuccess: (blob: Blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `logs_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('日志导出成功');
    },
    onError: () => {
      message.error('导出失败');
    },
  });

  // 导入日志
  const importMutation = useMutation({
    mutationFn: logsApi.import,
    onSuccess: (response: any) => {
      if (response.success) {
        message.success(response.message);
        queryClient.invalidateQueries({ queryKey: ['logs'] });
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
    setFilters(prev => ({ ...prev, search: value, page: 1 }));
  };

  const handleDateChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setFilters(prev => ({
        ...prev,
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
        page: 1
      }));
    } else {
      setFilters(prev => {
        const { start_date, end_date, ...rest } = prev;
        return { ...rest, page: 1 };
      });
    }
  };

  const handleStatusFilter = (status: string) => {
    setFilters(prev => ({ 
      ...prev, 
      status: status === 'all' ? undefined : status as 'success' | 'failed' | 'filtered', 
      page: 1 
    }));
  };

  const handleBatchDelete = () => {
    console.log('批量删除被调用，选中的行:', selectedRowKeys);
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的日志');
      return;
    }
    
    confirm({
      title: '确认删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 条日志吗？`,
      confirmText: '删除',
      cancelText: '取消',
      onConfirm: () => {
        console.log('确认删除，即将发送API请求:', selectedRowKeys);
        batchDeleteMutation.mutate(selectedRowKeys as number[]);
      },
    });
  };


  const getStatusTag = (status: string) => {
    const statusMap = {
      success: { color: 'success', text: '成功' },
      failed: { color: 'error', text: '失败' },
      pending: { color: 'processing', text: '处理中' },
      skipped: { color: 'default', text: '跳过' },
    };
    const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => (
        <span style={{ color: 'rgba(255,255,255,0.8)' }}>
          {text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-'}
        </span>
      ),
    },
    {
      title: '规则',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 120,
      filters: [...new Set((logsData?.items || []).map(log => log.rule_name || '未知规则'))].map(name => ({
        text: name,
        value: name,
      })),
      onFilter: (value: any, record: MessageLog) => (record.rule_name || '未知规则') === value,
      render: (text: string) => (
        <span style={{ color: 'white', fontWeight: 'bold' }}>{text || '未知规则'}</span>
      ),
    },
    {
      title: '源聊天',
      dataIndex: 'source_chat_name',
      key: 'source_chat_name',
      width: 120,
      filters: [...new Set((logsData?.items || []).map(log => {
        // 使用相同的getChatDisplayName逻辑
        const displayName = getChatDisplayName(log.source_chat_id || '');
        return displayName;
      }))].map(chat => ({
        text: chat,
        value: chat,
      })),
      onFilter: (value: any, record: MessageLog) => {
        const displayName = getChatDisplayName(record.source_chat_id || '');
        return displayName === value;
      },
      render: (_: string, record: MessageLog) => {
        const displayName = getChatDisplayName(record.source_chat_id || '');
        return <Tag color="blue">{displayName}</Tag>;
      },
    },
    {
      title: '目标聊天',
      dataIndex: 'target_chat_name',
      key: 'target_chat_name',
      width: 120,
      filters: [...new Set((logsData?.items || []).map(log => {
        // 使用相同的getChatDisplayName逻辑
        const displayName = getChatDisplayName(log.target_chat_id || '');
        return displayName;
      }))].map(chat => ({
        text: chat,
        value: chat,
      })),
      onFilter: (value: any, record: MessageLog) => {
        const displayName = getChatDisplayName(record.target_chat_id || '');
        return displayName === value;
      },
      render: (_: string, record: MessageLog) => {
        const displayName = getChatDisplayName(record.target_chat_id || '');
        return <Tag color="green">{displayName}</Tag>;
      },
    },
    {
      title: '消息内容',
      dataIndex: 'message_text',
      key: 'message_text',
      width: 280,
      render: (text: string) => (
        <div
          style={{
            color: 'rgba(255,255,255,0.9)',
            fontSize: '12px',
            lineHeight: '16px',
            maxHeight: '32px',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            wordBreak: 'break-all',
          }}
          title={text || '无内容'}
        >
          {text || '无内容'}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: MessageLog) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => {
                const statusText = record.status === 'success' ? '成功' : 
                                 record.status === 'failed' ? '失败' : 
                                 record.status === 'filtered' ? '已过滤' : record.status;
                
                const messageDetails = `规则: ${record.rule_name || '未知'}\n源聊天: ${record.source_chat_id || '未知'}\n目标聊天: ${record.target_chat_id || '未知'}\n状态: ${statusText}\n时间: ${dayjs(record.created_at).format('YYYY-MM-DD HH:mm:ss')}\n\n消息内容:\n${record.message_text || '无内容'}${record.error_message ? `\n\n错误信息:\n${record.error_message}` : ''}`;
                
                info({
                  title: '消息详情',
                  content: messageDetails,
                  confirmText: '我知道了',
                });
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ margin: 0, color: 'white' }}>消息日志</Title>
          <Space>
            <Search
              placeholder="搜索日志..."
              allowClear
              style={{ width: 200 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <RangePicker
              onChange={handleDateChange}
              style={{ width: 240 }}
            />
            <Select
              placeholder="状态筛选"
              style={{ width: 120 }}
              onChange={handleStatusFilter}
              allowClear
            >
              <Option value="all">全部</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
              <Option value="pending">处理中</Option>
              <Option value="skipped">跳过</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                console.log('刷新按钮被点击');
                queryClient.invalidateQueries({ queryKey: ['logs'] });
                refetch();
              }}
              loading={isLoading}
            >
              刷新
            </Button>
          </Space>
        </div>

        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBatchDelete}
                loading={batchDeleteMutation.isPending}
              >
                删除选中 ({selectedRowKeys.length})
              </Button>
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
              onClick={() => exportMutation.mutate(filters)}
              loading={exportMutation.isPending}
            >
              导出
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={logsData?.items || []}
          rowKey="id"
          loading={isLoading}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <div style={{ 
                padding: '50px', 
                textAlign: 'center',
                color: 'rgba(255, 255, 255, 0.6)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                <div style={{ fontSize: '16px', marginBottom: '8px' }}>暂无日志数据</div>
                <div style={{ fontSize: '14px' }}>转发规则执行后，日志将显示在这里</div>
              </div>
            )
          }}
          pagination={{
            current: filters.page,
            pageSize: filters.limit,
            total: logsData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条日志`,
            onChange: (page, pageSize) => {
              setFilters(prev => ({ ...prev, page, limit: pageSize }));
            },
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

export default LogsPage;
