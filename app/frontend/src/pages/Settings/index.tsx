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
  Alert,
  Slider,
  ColorPicker,
  Divider,
  Collapse
} from 'antd';
import { 
  SaveOutlined, 
  ExperimentOutlined,
  SettingOutlined,
  BgColorsOutlined,
  DownOutlined
} from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { settingsApi } from '../../services/settings';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

// 玻璃质感设置接口
interface GlassSettings {
  enabled: boolean;
  blur: number;
  brightness: number;
  saturation: number;
  color: {
    h: number;
    s: number;
    l: number;
    a: number;
  };
  texture: 'rice-paper' | 'egg-shell' | 'ink-jet' | 'coarse' | 'topology';
}

const defaultGlassSettings: GlassSettings = {
  enabled: true,
  blur: 5,
  brightness: 0.8,
  saturation: 1,
  color: {
    h: 180,
    s: 80,
    l: 10,
    a: 0.2
  },
  texture: 'rice-paper'
};

const textureOptions = [
  { value: 'rice-paper', label: 'Rice Paper', url: 'https://www.transparenttextures.com/patterns/rice-paper.png' },
  { value: 'egg-shell', label: 'Egg Shell', url: 'https://www.transparenttextures.com/patterns/egg-shell.png' },
  { value: 'ink-jet', label: 'Ink Jet', url: 'https://www.transparenttextures.com/patterns/ink-jet.png' },
  { value: 'coarse', label: 'Coarse', url: 'https://www.transparenttextures.com/patterns/coarse.png' },
  { value: 'topology', label: 'Topology', url: 'https://www.transparenttextures.com/patterns/topology.png' }
];

const SettingsPage: React.FC = () => {
  const [proxyForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('proxy');
  
  // 玻璃质感设置状态
  const [glassSettings, setGlassSettings] = useState<GlassSettings>(() => {
    try {
      const saved = localStorage.getItem('glass-settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        return { ...defaultGlassSettings, ...parsed };
      }
    } catch (error) {
      console.error('加载玻璃质感设置失败:', error);
      localStorage.removeItem('glass-settings');
    }
    return defaultGlassSettings;
  });

  // 应用玻璃质感设置到CSS变量
  const applyGlassSettings = (newSettings: GlassSettings) => {
    const root = document.documentElement;
    
    if (newSettings.enabled) {
      const { h, s, l, a } = newSettings.color;
      const textureUrl = textureOptions.find(t => t.value === newSettings.texture)?.url || '';
      
      root.style.setProperty('--glass-filter', 
        `blur(${newSettings.blur}px) brightness(${newSettings.brightness}) saturate(${newSettings.saturation})`
      );
      root.style.setProperty('--glass-color', 
        `hsl(${h} ${s}% ${l}% / ${a})`
      );
      root.style.setProperty('--glass-texture', 
        textureUrl ? `url("${textureUrl}")` : 'none'
      );
    } else {
      root.style.setProperty('--glass-filter', 'none');
      root.style.setProperty('--glass-color', 'rgba(255, 255, 255, 0.06)');
      root.style.setProperty('--glass-texture', 'none');
    }
  };

  // 初始化应用玻璃质感设置
  useEffect(() => {
    applyGlassSettings(glassSettings);
  }, [glassSettings]);

  // 更新玻璃质感设置
  const updateGlassSettings = (newSettings: Partial<GlassSettings>) => {
    const updated = { ...glassSettings, ...newSettings };
    setGlassSettings(updated);
    applyGlassSettings(updated);
    
    try {
      localStorage.setItem('glass-settings', JSON.stringify(updated));
    } catch (error) {
      console.error('保存玻璃质感设置失败:', error);
      message.error('保存设置失败');
    }
  };

  // 重置玻璃质感设置
  const resetGlassSettings = () => {
    setGlassSettings(defaultGlassSettings);
    applyGlassSettings(defaultGlassSettings);
    localStorage.setItem('glass-settings', JSON.stringify(defaultGlassSettings));
    message.success('已重置为默认设置');
  };

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
          <TabPane tab="界面设置" key="ui">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                message="界面外观设置"
                description="自定义应用的玻璃质感效果，打造个性化的视觉体验"
                type="info"
                showIcon
                style={{ marginBottom: '24px' }}
              />

              {/* 主开关 */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <Text style={{ color: 'white', fontSize: '16px', fontWeight: '600' }}>
                    <BgColorsOutlined style={{ marginRight: 8 }} />
                    启用玻璃质感效果
                  </Text>
                  <Switch
                    checked={glassSettings.enabled}
                    onChange={(checked) => updateGlassSettings({ enabled: checked })}
                    size="default"
                  />
                </div>
              </div>

              {glassSettings.enabled && (
                <Collapse
                  defaultActiveKey={['backdrop']}
                  expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
                  style={{ background: 'transparent', border: 'none' }}
                >
                  <Collapse.Panel 
                    header={<Text style={{ color: 'white', fontWeight: '500' }}>backdrop-filter 滤镜效果</Text>} 
                    key="backdrop"
                    style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                  >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      <div>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                          模糊强度: {glassSettings.blur}px
                        </Text>
                        <Slider
                          min={0}
                          max={20}
                          step={1}
                          value={glassSettings.blur}
                          onChange={(value) => updateGlassSettings({ blur: value })}
                          tooltip={{ formatter: (value) => `${value}px` }}
                        />
                      </div>
                      
                      <div>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                          亮度: {Math.round(glassSettings.brightness * 100)}%
                        </Text>
                        <Slider
                          min={0.1}
                          max={2.0}
                          step={0.1}
                          value={glassSettings.brightness}
                          onChange={(value) => updateGlassSettings({ brightness: value })}
                          tooltip={{ formatter: (value) => `${Math.round(value * 100)}%` }}
                        />
                      </div>
                      
                      <div>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                          饱和度: {Math.round(glassSettings.saturation * 100)}%
                        </Text>
                        <Slider
                          min={0.1}
                          max={3.0}
                          step={0.1}
                          value={glassSettings.saturation}
                          onChange={(value) => updateGlassSettings({ saturation: value })}
                          tooltip={{ formatter: (value) => `${Math.round(value * 100)}%` }}
                        />
                      </div>
                    </Space>
                  </Collapse.Panel>

                  <Collapse.Panel 
                    header={<Text style={{ color: 'white', fontWeight: '500' }}>color 背景颜色</Text>} 
                    key="color"
                    style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                  >
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      <div>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                          背景颜色
                        </Text>
                        <ColorPicker
                          value={`hsl(${glassSettings.color.h}, ${glassSettings.color.s}%, ${glassSettings.color.l}%)`}
                          onChange={(color) => {
                            const hsb = color.toHsb();
                            updateGlassSettings({
                              color: {
                                h: Math.round(hsb.h || 0),
                                s: Math.round(hsb.s || 0),
                                l: Math.round(hsb.b || 0), // HSB的b对应HSL的l
                                a: glassSettings.color.a
                              }
                            });
                          }}
                          showText={(color) => `HSL(${glassSettings.color.h}, ${glassSettings.color.s}%, ${glassSettings.color.l}%)`}
                          size="large"
                        />
                      </div>
                      
                      <div>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                          透明度: {Math.round(glassSettings.color.a * 100)}%
                        </Text>
                        <Slider
                          min={0.01}
                          max={0.5}
                          step={0.01}
                          value={glassSettings.color.a}
                          onChange={(value) => updateGlassSettings({ 
                            color: { ...glassSettings.color, a: value }
                          })}
                          tooltip={{ formatter: (value) => `${Math.round(value * 100)}%` }}
                        />
                      </div>
                    </Space>
                  </Collapse.Panel>

                  <Collapse.Panel 
                    header={<Text style={{ color: 'white', fontWeight: '500' }}>texture 纹理效果</Text>} 
                    key="texture"
                    style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                  >
                    <div>
                      <Text style={{ color: 'rgba(255, 255, 255, 0.9)', display: 'block', marginBottom: 8 }}>
                        选择纹理样式
                      </Text>
                      <Select
                        value={glassSettings.texture}
                        onChange={(value) => updateGlassSettings({ texture: value })}
                        style={{ width: '100%' }}
                        size="large"
                      >
                        {textureOptions.map(option => (
                          <Option key={option.value} value={option.value}>
                            {option.label}
                          </Option>
                        ))}
                      </Select>
                    </div>
                  </Collapse.Panel>
                </Collapse>
              )}

              <Divider style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }} />
              
              <Space>
                <Button
                  type="default"
                  onClick={resetGlassSettings}
                  style={{ minWidth: '120px' }}
                >
                  重置默认
                </Button>
              </Space>
            </Space>
          </TabPane>

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