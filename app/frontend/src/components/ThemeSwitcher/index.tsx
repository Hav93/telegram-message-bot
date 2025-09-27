import React, { useState, useRef } from 'react';
import { 
  Button, 
  Dropdown, 
  Space, 
  Modal, 
  Input, 
  message, 
  Typography,
  Upload,
  Tabs 
} from 'antd';
import { 
  BgColorsOutlined, 
  PictureOutlined, 
  CheckOutlined,
  SettingOutlined,
  UploadOutlined,
  LinkOutlined,
  InboxOutlined 
} from '@ant-design/icons';
import { useTheme, ThemeType } from '../../hooks/useTheme';
import type { MenuProps } from 'antd';

const { Text } = Typography;
const { Dragger } = Upload;

const ThemeSwitcher: React.FC = () => {
  const { themeConfig, changeTheme, getThemeName, defaultThemes } = useTheme();
  const [modalVisible, setModalVisible] = useState(false);
  const [customImageUrl, setCustomImageUrl] = useState(themeConfig.customImageUrl || '');
  const [selectedTheme, setSelectedTheme] = useState<ThemeType>(themeConfig.type);
  const [uploadMethod, setUploadMethod] = useState<'url' | 'file'>('url');
  const [uploadedImageBase64, setUploadedImageBase64] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 将文件转换为Base64
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  // 处理文件上传到服务器
  const handleFileUpload = async (file: File) => {
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      message.error('仅支持 JPG、PNG、WebP、GIF 格式的图片');
      return false;
    }

    // 验证文件大小 (最大20MB)
    const maxSize = 20 * 1024 * 1024; // 20MB
    if (file.size > maxSize) {
      message.error('图片大小不能超过 20MB');
      return false;
    }

    try {
      // 创建FormData上传到服务器
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await fetch('/api/system/upload-background', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('上传失败');
      }
      
      const result = await response.json();
      
      if (result.success) {
        setUploadedImageBase64(result.imageUrl); // 使用服务器返回的图片URL
        console.log('✅ 图片上传成功，URL:', result.imageUrl);
        message.success('图片上传成功');
      } else {
        throw new Error(result.message || '上传失败');
      }
      
      return false; // 阻止默认上传
    } catch (error) {
      console.error('❌ 图片上传失败:', error);
      message.error('图片上传失败，请重试');
      return false;
    }
  };

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
      if (uploadMethod === 'file') {
        // 使用上传的文件
        if (!uploadedImageBase64) {
          message.error('请先上传图片文件');
          return;
        }
        
        console.log('✅ 应用上传的图片URL:', uploadedImageBase64);
        changeTheme('custom', uploadedImageBase64);
        message.success('自定义背景已应用');
        setModalVisible(false);
        
      } else {
        // 使用URL链接
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
        
        // 预加载图片验证
        const img = new Image();
        img.crossOrigin = 'anonymous'; // 尝试跨域访问
        
        img.onload = () => {
          console.log('✅ 图片加载成功:', customImageUrl);
          changeTheme('custom', customImageUrl);
          message.success('自定义背景已应用');
          setModalVisible(false);
        };
        
        img.onerror = () => {
          console.error('❌ 图片加载失败:', customImageUrl);
          message.error('图片加载失败，请检查URL是否正确或尝试其他图片');
        };
        
        // 开始加载图片
        img.src = customImageUrl;
      }
    } else {
      changeTheme(selectedTheme);
      setModalVisible(false);
    }
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
        className="glass-modal theme-modal"
        width={600}
        styles={{
          content: {
            background: 'transparent',
            padding: 0
          },
          body: {
            background: 'transparent',
            padding: '16px 24px'
          },
          footer: {
            background: 'transparent',
            borderTop: 'none'
          }
        }}
      >
        <div>
          <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 16, display: 'block' }}>
            选择背景主题：
          </Text>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {themeOptions.map(option => (
              <div
                key={option.key}
                onClick={() => setSelectedTheme(option.key as ThemeType)}
                className={`theme-card ${selectedTheme === option.key ? 'selected' : ''}`}
              >
                {option.preview && (
                  <div
                    className="theme-preview"
                    style={{
                      background: option.preview
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
            ))}
          </div>

          {selectedTheme === 'custom' && (
            <div style={{ marginTop: '20px' }}>
              <Tabs
                activeKey={uploadMethod}
                onChange={(key) => setUploadMethod(key as 'url' | 'file')}
                items={[
                  {
                    key: 'url',
                    label: (
                      <span style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                        <LinkOutlined style={{ marginRight: 4 }} />
                        图片链接
                      </span>
                    ),
                    children: (
                      <div style={{ paddingTop: '12px' }}>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 8, display: 'block' }}>
                          输入图片URL：
                        </Text>
                        <Input
                          placeholder="https://example.com/image.jpg"
                          value={customImageUrl}
                          onChange={(e) => setCustomImageUrl(e.target.value)}
                          prefix={<LinkOutlined />}
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
                          🔸 建议使用直接图片链接 (以 .jpg/.png/.webp 结尾)<br/>
                          🔸 确保图片允许跨域访问，避免使用需要登录的链接<br/>
                          🔸 推荐使用免费图床：sm.ms、imgbb.com、telegraph.ph
                        </Text>
                      </div>
                    )
                  },
                  {
                    key: 'file',
                    label: (
                      <span style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                        <UploadOutlined style={{ marginRight: 4 }} />
                        本地上传
                      </span>
                    ),
                    children: (
                      <div style={{ paddingTop: '12px' }}>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 8, display: 'block' }}>
                          选择本地图片：
                        </Text>
                        <Dragger
                          beforeUpload={handleFileUpload}
                          showUploadList={false}
                          accept="image/*"
                          style={{
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '2px dashed rgba(255, 255, 255, 0.3)',
                            borderRadius: '8px',
                          }}
                        >
                          <p className="ant-upload-drag-icon">
                            <InboxOutlined style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '48px' }} />
                          </p>
                          <p style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '16px', margin: '0 0 4px 0' }}>
                            点击或拖拽图片到此区域上传
                          </p>
                          <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '12px', margin: 0 }}>
                            支持 JPG、PNG、WebP、GIF 格式，最大 20MB
                          </p>
                        </Dragger>
                        
                               {uploadedImageBase64 && (
                                 <div style={{ 
                                   marginTop: '12px', 
                                   padding: '8px', 
                                   background: 'rgba(82, 196, 26, 0.1)',
                                   border: '1px solid rgba(82, 196, 26, 0.3)',
                                   borderRadius: '6px'
                                 }}>
                                   <Text style={{ color: '#52c41a', fontSize: '12px' }}>
                                     ✅ 图片上传成功，已保存到服务器
                                   </Text>
                                   <div style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '10px', marginTop: '4px' }}>
                                     {uploadedImageBase64}
                                   </div>
                                 </div>
                               )}
                      </div>
                    )
                  }
                ]}
                style={{
                  '& .ant-tabs-tab': {
                    color: 'rgba(255, 255, 255, 0.7) !important'
                  },
                  '& .ant-tabs-tab-active': {
                    color: '#1890ff !important'
                  }
                }}
              />
            </div>
          )}
        </div>
      </Modal>
    </>
  );
};

export default ThemeSwitcher;

