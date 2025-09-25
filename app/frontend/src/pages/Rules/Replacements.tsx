import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Switch,
  InputNumber,
  message,
  Tooltip
} from 'antd';
import '../../components/common/TooltipFix.css';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCustomModal } from '../../hooks/useCustomModal';
import { replaceRulesApi } from '../../services/rules';

const { Title } = Typography;
const { TextArea } = Input;

interface ReplaceRule {
  id: number;
  rule_id: number;
  name?: string;
  pattern: string;
  replacement: string;
  priority: number;
  is_regex: boolean;
  is_active: boolean;
  created_at: string;
}

const ReplacementsPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const ruleId = id ? parseInt(id, 10) : 0;
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ReplaceRule | null>(null);
  const [form] = Form.useForm();
  const { confirm, Modal: CustomModalComponent } = useCustomModal();

  // 获取替换规则列表
  const { data: replaceRules = [], isLoading } = useQuery({
    queryKey: ['replace-rules', ruleId],
    queryFn: () => replaceRulesApi.getByRule(ruleId),
    enabled: !!ruleId,
  });

  // 创建替换规则
  const createMutation = useMutation({
    mutationFn: replaceRulesApi.create,
    onSuccess: () => {
      message.success('替换规则添加成功');
      queryClient.invalidateQueries({ queryKey: ['replace-rules', ruleId] });
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: () => {
      message.error('替换规则添加失败');
    },
  });

  // 更新替换规则
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<ReplaceRule>) => 
      replaceRulesApi.update(id, data),
    onSuccess: () => {
      message.success('替换规则更新成功');
      queryClient.invalidateQueries({ queryKey: ['replace-rules', ruleId] });
      setIsModalVisible(false);
      setEditingRule(null);
      form.resetFields();
    },
    onError: () => {
      message.error('替换规则更新失败');
    },
  });

  // 删除替换规则
  const deleteMutation = useMutation({
    mutationFn: replaceRulesApi.delete,
    onSuccess: () => {
      message.success('替换规则删除成功');
      queryClient.invalidateQueries({ queryKey: ['replace-rules', ruleId] });
    },
    onError: () => {
      message.error('替换规则删除失败');
    },
  });

  const handleAdd = () => {
    setEditingRule(null);
    form.resetFields();
    form.setFieldsValue({
      priority: 1,
      is_regex: false,
      is_active: true,
    });
    setIsModalVisible(true);
  };

  const handleEdit = (rule: ReplaceRule) => {
    setEditingRule(rule);
    form.setFieldsValue(rule);
    setIsModalVisible(true);
  };

  const handleDelete = (rule: ReplaceRule) => {
    confirm({
      title: '确认删除',
      content: `确定要删除替换规则"${rule.name || rule.pattern}"吗？`,
      confirmText: '删除',
      cancelText: '取消',
      onConfirm: () => deleteMutation.mutate(rule.id),
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingRule) {
        updateMutation.mutate({ id: editingRule.id, ...values });
      } else {
        createMutation.mutate({ rule_id: ruleId, ...values });
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ReplaceRule) => (
        <span style={{ color: 'white' }}>
          {text || `替换规则 #${record.id}`}
        </span>
      ),
    },
    {
      title: '匹配模式',
      dataIndex: 'pattern',
      key: 'pattern',
      render: (text: string, record: ReplaceRule) => (
        <div>
          <span style={{ 
            color: 'white', 
            fontFamily: 'monospace',
            backgroundColor: 'rgba(255,255,255,0.1)',
            padding: '2px 6px',
            borderRadius: '4px'
          }}>
            {text}
          </span>
          {record.is_regex && (
            <span style={{ 
              color: '#1890ff', 
              fontSize: '12px',
              marginLeft: '8px'
            }}>
              正则
            </span>
          )}
        </div>
      ),
    },
    {
      title: '替换内容',
      dataIndex: 'replacement',
      key: 'replacement',
      render: (text: string) => (
        <span style={{ 
          color: '#52c41a', 
          fontFamily: 'monospace',
          backgroundColor: 'rgba(82,196,26,0.1)',
          padding: '2px 6px',
          borderRadius: '4px'
        }}>
          {text}
        </span>
      ),
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: number) => (
        <span style={{ color: 'white' }}>{priority}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (is_active: boolean) => (
        <span style={{ 
          color: is_active ? '#52c41a' : '#d9d9d9',
          fontWeight: 'bold'
        }}>
          {is_active ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: ReplaceRule) => (
        <Space>
          <Tooltip title="编辑替换规则">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除替换规则">
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              loading={deleteMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/rules')}
            >
              返回规则列表
            </Button>
            <Title level={2} style={{ margin: 0, color: 'white' }}>
              替换规则管理 (规则 #{ruleId})
            </Title>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加替换规则
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={replaceRules}
          rowKey="id"
          loading={isLoading}
          locale={{
            emptyText: (
              <div style={{ 
                padding: '50px', 
                textAlign: 'center',
                color: 'rgba(255, 255, 255, 0.6)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔄</div>
                <div style={{ fontSize: '16px', marginBottom: '8px' }}>暂无替换规则</div>
                <div style={{ fontSize: '14px' }}>点击"添加替换规则"开始设置文本替换</div>
              </div>
            )
          }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个替换规则`,
          }}
          style={{ 
            background: 'transparent',
          }}
        />
      </Card>

      <Modal
        title={editingRule ? '编辑替换规则' : '添加替换规则'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingRule(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="规则名称"
            name="name"
            tooltip="可选，用于标识该替换规则"
          >
            <Input placeholder="输入规则名称（可选）" />
          </Form.Item>
          <Form.Item
            label="匹配模式"
            name="pattern"
            rules={[{ required: true, message: '请输入匹配模式' }]}
            tooltip="要匹配的文本内容，可以是普通文本或正则表达式"
          >
            <TextArea 
              placeholder="输入要匹配的文本或正则表达式"
              rows={3}
            />
          </Form.Item>
          <Form.Item
            label="替换内容"
            name="replacement"
            rules={[{ required: true, message: '请输入替换内容' }]}
            tooltip="匹配到的内容将被替换为此内容。如果使用正则表达式，可以使用 $1, $2 等引用捕获组"
          >
            <TextArea 
              placeholder="输入替换后的内容"
              rows={3}
            />
          </Form.Item>
          <Form.Item
            label="优先级"
            name="priority"
            tooltip="数字越小优先级越高，优先级高的规则会先执行"
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            label="正则表达式"
            name="is_regex"
            valuePropName="checked"
            tooltip="是否将匹配模式视为正则表达式"
          >
            <Switch
              checkedChildren="正则"
              unCheckedChildren="普通"
            />
          </Form.Item>
          <Form.Item
            label="启用状态"
            name="is_active"
            valuePropName="checked"
          >
            <Switch
              checkedChildren="启用"
              unCheckedChildren="禁用"
            />
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 自定义Modal */}
      {CustomModalComponent}
    </div>
  );
};

export default ReplacementsPage;
