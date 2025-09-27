import React, { useState } from 'react';
import { 
  Button, 
  Dropdown, 
  Space, 
  Modal, 
  Input, 
  message, 
  Radio, 
  Card,
  Typography 
} from 'antd';
import { 
  BgColorsOutlined, 
  PictureOutlined, 
  CheckOutlined,
  SettingOutlined 
} from '@ant-design/icons';
import { useTheme, ThemeType } from '../../hooks/useTheme';
import type { MenuProps } from 'antd';

const { Text } = Typography;

const ThemeSwitcher: React.FC = () => {
  const { themeConfig, changeTheme, getThemeName, defaultThemes } = useTheme();
  const [modalVisible, setModalVisible] = useState(false);
  const [customImageUrl, setCustomImageUrl] = useState(themeConfig.customImageUrl || '');
  const [selectedTheme, setSelectedTheme] = useState<ThemeType>(themeConfig.type);

  const handleThemeChange = (type: ThemeType) => {
    if (type === 'custom') {
      setSelectedTheme(type);
      setModalVisible(true);
    } else {
      changeTheme(type);
    }
  };

  const handleCustomThemeConfirm = () => {
    if (selectedTheme === 'custom') {
      if (!customImageUrl.trim()) {
        message.error('请输入图片URL');
        return;
      }
      
      // 简单验证URL格式
      try {
        new URL(customImageUrl);
      } catch {
        message.error('请输入有效的图片URL');
        return;
      }
      
      changeTheme('custom', customImageUrl);
      message.success('自定义背景已应用');
    } else {
      changeTheme(selectedTheme);
    }
    setModalVisible(false);
  };

  const themeOptions = [
    {
      key: 'gradient',
      label: '紫蓝渐变',
      icon: <BgColorsOutlined style={{ color: '#667eea' }} />,
      preview: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    },
    {
      key: 'dark',
      label: '深色主题',
      icon: <BgColorsOutlined style={{ color: '#1a1a1a' }} />,
      preview: '#1a1a1a'
    },
    {
      key: 'gray',
      label: '灰色主题',
      icon: <BgColorsOutlined style={{ color: '#2c3e50' }} />,
      preview: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)'
    },
    {
      key: 'custom',
      label: '自定义背景',
      icon: <PictureOutlined style={{ color: '#fa8c16' }} />,
      preview: null
    }
  ];

  const menuItems: MenuProps['items'] = themeOptions.map(option => ({
    key: option.key,
    label: (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        minWidth: '160px'
      }}>
        <Space>
          {option.icon}
          <span>{option.label}</span>
        </Space>
        {themeConfig.type === option.key && (
          <CheckOutlined style={{ color: '#52c41a' }} />
        )}
      </div>
    ),
    onClick: () => handleThemeChange(option.key as ThemeType)
  }));

  return (
    <>
      <Dropdown
        menu={{ items: menuItems }}
        trigger={['click']}
        placement="bottomRight"
      >
        <Button
          type="text"
          icon={<BgColorsOutlined />}
          style={{ 
            color: 'rgba(255, 255, 255, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)'
          }}
        >
          {getThemeName()}
        </Button>
      </Dropdown>

      <Modal
        title={
          <span style={{ color: '#ffffff' }}>
            <SettingOutlined style={{ marginRight: 8 }} />
            主题设置
          </span>
        }
        open={modalVisible}
        onOk={handleCustomThemeConfirm}
        onCancel={() => {
          setModalVisible(false);
          setSelectedTheme(themeConfig.type);
        }}
        okText="应用"
        cancelText="取消"
        className="glass-modal"
        width={600}
      >
        <div style={{ padding: '16px 0' }}>
          <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 16, display: 'block' }}>
            选择背景主题：
          </Text>
          
          <Radio.Group
            value={selectedTheme}
            onChange={(e) => setSelectedTheme(e.target.value)}
            style={{ width: '100%' }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {themeOptions.map(option => (
                <Radio.Button 
                  key={option.key} 
                  value={option.key}
                  style={{ height: 'auto', padding: 0 }}
                >
                  <Card
                    size="small"
                    style={{ 
                      margin: 0,
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: selectedTheme === option.key ? 
                        '2px solid #1890ff' : 
                        '1px solid rgba(255, 255, 255, 0.2)',
                      backdropFilter: 'blur(5px)'
                    }}
                    bodyStyle={{ padding: '12px' }}
                  >
                    <div style={{ textAlign: 'center' }}>
                      {option.preview && (
                        <div
                          style={{
                            width: '100%',
                            height: '40px',
                            background: option.preview,
                            borderRadius: '4px',
                            marginBottom: '8px',
                            border: '1px solid rgba(255, 255, 255, 0.2)'
                          }}
                        />
                      )}
                      <Space>
                        {option.icon}
                        <Text style={{ color: '#ffffff', fontSize: '12px' }}>
                          {option.label}
                        </Text>
                      </Space>
                    </div>
                  </Card>
                </Radio.Button>
              ))}
            </div>
          </Radio.Group>

          {selectedTheme === 'custom' && (
            <div style={{ marginTop: '20px' }}>
              <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 8, display: 'block' }}>
                图片URL：
              </Text>
              <Input
                placeholder="请输入图片URL (支持 https://... 或图床链接)"
                value={customImageUrl}
                onChange={(e) => setCustomImageUrl(e.target.value)}
                prefix={<PictureOutlined />}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: '#ffffff'
                }}
              />
              <Text 
                type="secondary" 
                style={{ 
                  color: 'rgba(255, 255, 255, 0.6)', 
                  fontSize: '12px',
                  marginTop: '8px',
                  display: 'block'
                }}
              >
                建议使用高质量图片，支持 JPG、PNG、WebP 格式
              </Text>
            </div>
          )}
        </div>
      </Modal>
    </>
  );
};

export default ThemeSwitcher;

