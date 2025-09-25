import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Space, 
  Typography,
  Tabs,
  Switch,
  InputNumber,
  Select,
  message,
  Alert
} from 'antd';
import { 
  SaveOutlined, 
  ExperimentOutlined
} from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { settingsApi } from '../../services/settings';

const { Title } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const SettingsPage: React.FC = () => {
  const [proxyForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('proxy');

  // 获取当前配置
  const { data: currentConfig, isLoading, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.getCurrentConfig,
  });

  // 当获取到配置数据时，填充表单
  useEffect(() => {
    if (currentConfig) {
      proxyForm.setFieldsValue({
        enable_proxy: currentConfig.enable_proxy,
        proxy_type: currentConfig.proxy_type,
        proxy_host: currentConfig.proxy_host,
        proxy_port: currentConfig.proxy_port,
        proxy_username: currentConfig.proxy_username,
        proxy_password: currentConfig.proxy_password === '***' ? '' : currentConfig.proxy_password,
      });
      
      systemForm.setFieldsValue({
        api_id: currentConfig.api_id,
        api_hash: currentConfig.api_hash,
        bot_token: currentConfig.bot_token,
        phone_number: currentConfig.phone_number,
        admin_user_ids: currentConfig.admin_user_ids,
        enable_log_cleanup: currentConfig.enable_log_cleanup,
        log_retention_days: currentConfig.log_retention_days,
        log_cleanup_time: currentConfig.log_cleanup_time,
        max_log_size: currentConfig.max_log_size,
      });
    }
  }, [currentConfig, proxyForm, systemForm]);

  // 模拟代理测试功能
  const testProxyMutation = useMutation({
    mutationFn: async (values: any) => {
      // 简单的客户端代理测试
      const response = await fetch(`http://${values.proxy_host}:${values.proxy_port}`, {
        method: 'GET',
        mode: 'no-cors', // 避免CORS问题
      }).catch(() => null);
      
      return {
        success: !!response,
        message: response ? '代理连接测试完成' : '代理连接失败'
      };
    },
    onSuccess: (result) => {
      if (result.success) {
        message.success({
          content: '✅ 代理连接测试完成！',
          duration: 3,
        });
      } else {
        message.error({
          content: `❌ 代理测试失败: ${result.message}`,
          duration: 4,
        });
      }
    },
    onError: (error: any) => {
      message.error({
        content: `❌ 代理测试失败: ${error.message || '网络错误'}`,
        duration: 4,
      });
    },
  });

  // 保存设置到后端
  const saveMutation = useMutation({
    mutationFn: settingsApi.saveSettings,
    onSuccess: (result) => {
      message.success({
        content: `✅ ${result.message || '配置保存成功！'}`,
        duration: 3,
      });
      // 重新获取配置以确保数据同步
      refetch();
    },
    onError: (error: any) => {
      message.error({
        content: `❌ 配置保存失败: ${error.message}`,
        duration: 4,
      });
    },
  });

  // 重启Telegram客户端
  const restartClientMutation = useMutation({
    mutationFn: settingsApi.restartClient,
    onSuccess: (result) => {
      message.success({
        content: `✅ ${result.message || 'Telegram客户端重启成功！'}`,
        duration: 3,
      });
    },
    onError: (error: any) => {
      message.error({
        content: `❌ 客户端重启失败: ${error.message}`,
        duration: 4,
      });
    },
  });

  // 代理配置保存
  const handleProxySave = async () => {
    try {
      const formValues = proxyForm.getFieldsValue();
      console.log('保存代理配置:', formValues);
      
      // 合并当前配置和代理表单数据
      const allSettings = {
        ...currentConfig,
        ...formValues
      };
      
      await saveMutation.mutateAsync(allSettings);
    } catch (error) {
      console.error('代理配置保存失败:', error);
      message.error('代理配置保存失败');
    }
  };

  // 系统配置保存
  const handleSystemSave = async () => {
    try {
      const formValues = systemForm.getFieldsValue();
      console.log('保存系统配置:', formValues);
      
      // 合并当前配置和系统表单数据
      const allSettings = {
        ...currentConfig,
        ...formValues
      };
      
      await saveMutation.mutateAsync(allSettings);
    } catch (error) {
      console.error('系统配置保存失败:', error);
      message.error('系统配置保存失败');
    }
  };

  const handleProxyTest = async () => {
    try {
      const values = await proxyForm.validateFields();
      await testProxyMutation.mutateAsync(values);
    } catch (error) {
      console.error('代理测试失败:', error);
    }
  };

  // 重启Telegram客户端
  const handleRestartClient = async () => {
    try {
      await restartClientMutation.mutateAsync();
    } catch (error) {
      console.error('重启客户端失败:', error);
    }
  };

  if (isLoading) {
    return (
      <div style={{ padding: '24px' }}>
        <Card className="glass-card">
          <div style={{ textAlign: 'center', padding: '50px', color: 'white' }}>
            <div style={{ fontSize: '16px' }}>正在加载配置...</div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <Title level={2} style={{ color: 'white', marginBottom: '24px' }}>系统设置</Title>
        
        <Alert
          message="Telegram配置已迁移"
          description="Telegram客户端配置功能已迁移到「客户端管理」页面，您可以在那里添加和管理多个Telegram客户端。"
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />
        
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="代理设置" key="proxy">
            <Form
              form={proxyForm}
              layout="vertical"
              initialValues={{
                enable_proxy: false,
                proxy_type: 'http',
                proxy_host: '127.0.0.1',
                proxy_port: 1080,
                proxy_username: '',
                proxy_password: ''
              }}
            >
              <Alert
                message="代理设置"
                description="如果您的网络无法直接访问Telegram，请配置代理服务器"
                type="info"
                showIcon
                style={{ marginBottom: '24px' }}
              />

              <Form.Item
                label={<span style={{ color: 'white' }}>启用代理</span>}
                name="enable_proxy"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>代理类型</span>}
                name="proxy_type"
              >
                <Select placeholder="选择代理类型">
                  <Option value="http">HTTP</Option>
                  <Option value="https">HTTPS</Option>
                  <Option value="socks4">SOCKS4</Option>
                  <Option value="socks5">SOCKS5</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>代理服务器</span>}
                name="proxy_host"
              >
                <Input placeholder="代理服务器地址" />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>端口</span>}
                name="proxy_port"
              >
                <InputNumber 
                  placeholder="端口号" 
                  min={1} 
                  max={65535} 
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>用户名</span>}
                name="proxy_username"
              >
                <Input placeholder="用户名 (可选)" />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>密码</span>}
                name="proxy_password"
              >
                <Input.Password placeholder="密码 (可选)" />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  icon={<ExperimentOutlined />}
                  onClick={handleProxyTest}
                  loading={testProxyMutation.isPending}
                >
                  {testProxyMutation.isPending ? '测试中...' : '测试代理'}
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleProxySave}
                  loading={saveMutation.isPending}
                >
                  {saveMutation.isPending ? '保存中...' : '保存代理配置'}
                </Button>
              </Space>
            </Form>
          </TabPane>

          <TabPane tab="系统设置" key="system">
            <Form
              form={systemForm}
              layout="vertical"
              initialValues={{
                log_level: 'INFO',
                max_log_size: 100,
                enable_log_cleanup: true,
                log_retention_days: 30,
                log_cleanup_time: '0 2 * * *'
              }}
            >
              <Form.Item
                label={<span style={{ color: 'white' }}>日志级别</span>}
                name="log_level"
              >
                <Select placeholder="选择日志级别">
                  <Option value="DEBUG">DEBUG</Option>
                  <Option value="INFO">INFO</Option>
                  <Option value="WARNING">WARNING</Option>
                  <Option value="ERROR">ERROR</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>最大日志大小(MB)</span>}
                name="max_log_size"
              >
                <InputNumber 
                  placeholder="最大日志大小" 
                  min={10} 
                  max={1000} 
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>自动清理日志</span>}
                name="enable_log_cleanup"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>日志保留天数</span>}
                name="log_retention_days"
              >
                <InputNumber 
                  placeholder="日志保留天数" 
                  min={1} 
                  max={365} 
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item
                label={<span style={{ color: 'white' }}>清理时间 (Cron表达式)</span>}
                name="log_cleanup_time"
                tooltip="使用5位cron表达式格式: 分 时 日 月 周，例如: 0 2 * * * (每天凌晨2点)"
              >
                <Input 
                  placeholder="例如: 0 2 * * * (每天凌晨2点)" 
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSystemSave}
                  loading={saveMutation.isPending}
                >
                  {saveMutation.isPending ? '保存中...' : '保存系统配置'}
                </Button>
              </Space>
            </Form>
          </TabPane>

          <TabPane tab="Telegram配置" key="telegram">
            <div>
              <Alert
                message="Telegram客户端管理"
                description="配置保存后，需要重启Telegram客户端以应用新的设置。请确保您已在「客户端管理」页面完成了基础配置。"
                type="warning"
                showIcon
                style={{ marginBottom: '24px' }}
              />

              <Space size="large" direction="vertical" style={{ width: '100%' }}>
                <Card size="small" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  <div style={{ color: 'white' }}>
                    <h4>🔄 客户端控制</h4>
                    <p>当您修改了Telegram API配置（API_ID、API_HASH等）后，需要重启客户端使配置生效。</p>
                    
                    <Button
                      type="primary"
                      size="large"
                      onClick={handleRestartClient}
                      loading={restartClientMutation.isPending}
                      style={{ marginTop: '12px' }}
                    >
                      {restartClientMutation.isPending ? '重启中...' : '🚀 重启Telegram客户端'}
                    </Button>
                  </div>
                </Card>

                <Card size="small" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  <div style={{ color: 'white' }}>
                    <h4>💡 使用说明</h4>
                    <ul style={{ paddingLeft: '20px' }}>
                      <li>首次启动：如果是无配置启动，配置后点击重启按钮即可开始使用</li>
                      <li>配置更新：修改API配置或代理设置后，建议重启客户端</li>
                      <li>故障恢复：如果客户端出现连接问题，可以尝试重启</li>
                    </ul>
                  </div>
                </Card>
              </Space>
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default SettingsPage;