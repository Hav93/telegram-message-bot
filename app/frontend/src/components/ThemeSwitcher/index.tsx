import React, { useState } from 'react';
import { 
  Button, 
  Dropdown, 
  Space, 
  Modal, 
  Input, 
  message, 
  Typography,
  Upload,
  Tabs,
  Image,
  Tooltip,
  Card,
  Empty
} from 'antd';
import { 
  BgColorsOutlined, 
  PictureOutlined, 
  CheckOutlined,
  SettingOutlined,
  UploadOutlined,
  LinkOutlined,
  InboxOutlined,
  DeleteOutlined,
  EyeOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { useTheme, ThemeType } from '../../hooks/useTheme';
import type { MenuProps } from 'antd';

interface BackgroundImage {
  filename: string;
  url: string;
  size: number;
  uploaded_at: string;
  modified_at: string;
}

const { Text } = Typography;
const { Dragger } = Upload;

const ThemeSwitcher: React.FC = () => {
  const { themeConfig, changeTheme, getThemeName } = useTheme();
  const [modalVisible, setModalVisible] = useState(false);
  const [customImageUrl, setCustomImageUrl] = useState(themeConfig.customImageUrl || '');
  const [selectedTheme, setSelectedTheme] = useState<ThemeType>(themeConfig.type);
  const [uploadMethod, setUploadMethod] = useState<'url' | 'file' | 'history'>('url');
  const [uploadedImageBase64, setUploadedImageBase64] = useState<string>('');
  const [historyImages, setHistoryImages] = useState<BackgroundImage[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedHistoryImage, setSelectedHistoryImage] = useState<string>('');

  // 获取历史背景图片
  const fetchHistoryImages = async () => {
    setLoadingHistory(true);
    try {
      console.log('🔄 开始获取历史背景图片...');
      const response = await fetch('/api/system/backgrounds');
      console.log('📡 API响应状态:', response.status, response.statusText);
      
      const result = await response.json();
      console.log('📋 API响应数据:', result);
      
      if (result.success) {
        setHistoryImages(result.backgrounds);
        console.log('✅ 获取历史背景图片成功:', result.backgrounds);
        message.success(`成功加载 ${result.backgrounds.length} 张历史图片`);
      } else {
        console.error('❌ 获取历史背景图片失败:', result.message);
        message.error(`获取历史图片失败: ${result.message}`);
      }
    } catch (error) {
      console.error('❌ 获取历史背景图片失败:', error);
      message.error(`网络错误: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setLoadingHistory(false);
    }
  };

  // 删除背景图片
  const deleteHistoryImage = async (filename: string) => {
    try {
      console.log('🗑️ 开始删除背景图片:', filename);
      const deleteUrl = `/api/system/backgrounds/${filename}`;
      console.log('🔗 删除URL:', deleteUrl);
      
      const response = await fetch(deleteUrl, {
        method: 'DELETE'
      });
      
      console.log('📡 删除API响应状态:', response.status, response.statusText);
      const result = await response.json();
      console.log('📋 删除API响应数据:', result);
      
      if (result.success) {
        message.success('删除成功');
        console.log('✅ 图片删除成功，重新获取列表...');
        fetchHistoryImages(); // 重新获取列表
        
        // 如果删除的是当前使用的背景，切换回默认主题
        if (themeConfig.customImageUrl?.includes(filename)) {
          changeTheme('gradient');
          message.info('当前背景已删除，已切换回默认主题');
        }
      } else {
        console.error('❌ 删除失败:', result.message);
        message.error(`删除失败: ${result.message}`);
      }
    } catch (error) {
      console.error('❌ 删除背景图片失败:', error);
      message.error(`删除失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化时间
  const formatDate = (isoString: string): string => {
    return new Date(isoString).toLocaleString('zh-CN');
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
        
      } else if (uploadMethod === 'history') {
        // 使用历史图片
        if (!selectedHistoryImage) {
          message.error('请选择一张历史图片');
          return;
        }
        
        console.log('✅ 应用历史图片:', selectedHistoryImage);
        changeTheme('custom', selectedHistoryImage);
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
        const img = new window.Image();
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
        
        // 添加超时处理
        setTimeout(() => {
          if (!img.complete) {
            console.error('❌ 图片加载超时:', customImageUrl);
            message.error('图片加载超时，请检查URL或尝试其他图片');
          }
        }, 10000); // 10秒超时
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
        className="glass-modal theme-settings-modal"
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
                onChange={(key) => {
                  const newMethod = key as 'url' | 'file' | 'history';
                  setUploadMethod(newMethod);
                  if (newMethod === 'history') {
                    fetchHistoryImages();
                  }
                }}
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
                            <div style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '10px', marginTop: '4px', wordBreak: 'break-all' }}>
                              {uploadedImageBase64.length > 50 ? uploadedImageBase64.substring(0, 50) + '...' : uploadedImageBase64}
                                   </div>
                                 </div>
                               )}
                      </div>
                    )
                  },
                  {
                    key: 'history',
                    label: (
                      <span style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                        <HistoryOutlined style={{ marginRight: 4 }} />
                        历史图片
                      </span>
                    ),
                    children: (
                      <div style={{ paddingTop: '12px' }}>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: 8, display: 'block' }}>
                          选择已上传的图片：
                        </Text>
                        
                        {loadingHistory ? (
                          <div style={{ textAlign: 'center', padding: '20px', color: 'rgba(255, 255, 255, 0.6)' }}>
                            加载中...
                          </div>
                        ) : historyImages.length === 0 ? (
                          <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description={
                              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                                暂无历史图片
                              </span>
                            }
                            style={{
                              background: 'rgba(255, 255, 255, 0.05)',
                              borderRadius: '8px',
                              padding: '20px',
                              border: '1px solid rgba(255, 255, 255, 0.1)'
                            }}
                          />
                        ) : (
                          <div style={{ 
                            maxHeight: '300px', 
                            overflowY: 'auto',
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                            gap: '8px'
                          }}>
                            {historyImages.map((img) => (
                              <Card
                                key={img.filename}
                                size="small"
                                hoverable
                                style={{
                                  background: selectedHistoryImage === img.url 
                                    ? 'rgba(24, 144, 255, 0.3)' 
                                    : 'rgba(255, 255, 255, 0.05)',
                                  border: selectedHistoryImage === img.url 
                                    ? '2px solid #1890ff' 
                                    : '1px solid rgba(255, 255, 255, 0.1)',
                                  borderRadius: '8px',
                                  cursor: 'pointer',
                                  transition: 'all 0.3s ease',
                                  transform: selectedHistoryImage === img.url ? 'scale(1.02)' : 'scale(1)',
                                  boxShadow: selectedHistoryImage === img.url 
                                    ? '0 4px 16px rgba(24, 144, 255, 0.4), 0 0 0 1px rgba(24, 144, 255, 0.2)' 
                                    : '0 2px 8px rgba(0, 0, 0, 0.1)'
                                }}
                                onClick={() => setSelectedHistoryImage(img.url)}
                                bodyStyle={{ padding: '8px' }}
                                actions={[
                                  <Tooltip title="预览" key="preview">
                                    <EyeOutlined 
                                      style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '16px' }}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        console.log('👁️ 预览图片:', img.filename, img.url);
                                        Modal.info({
                                          title: `图片预览 - ${img.filename}`,
                                          content: (
                                            <div style={{ textAlign: 'center', padding: '20px' }}>
                                              <img 
                                                src={img.url} 
                                                alt={img.filename}
                                                style={{ 
                                                  maxWidth: '100%', 
                                                  maxHeight: '400px',
                                                  borderRadius: '8px',
                                                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
                                                }}
                                                onLoad={() => {
                                                  console.log('✅ 预览图片加载成功:', img.url);
                                                }}
                                                onError={(e) => {
                                                  console.error('❌ 预览图片加载失败:', img.url);
                                                  const target = e.target as HTMLImageElement;
                                                  target.style.display = 'none';
                                                  const errorDiv = target.nextElementSibling as HTMLElement;
                                                  if (errorDiv) {
                                                    errorDiv.style.display = 'block';
                                                  }
                                                }}
                                              />
                                              <div style={{ 
                                                display: 'none', 
                                                color: '#ff4d4f', 
                                                marginTop: '20px',
                                                fontSize: '14px'
                                              }}>
                                                图片加载失败: {img.url}
                                              </div>
                                              <div style={{ 
                                                marginTop: '16px',
                                                fontSize: '12px',
                                                color: '#666',
                                                wordBreak: 'break-all'
                                              }}>
                                                文件名: {img.filename}<br/>
                                                大小: {formatFileSize(img.size)}<br/>
                                                URL: {img.url}
                                              </div>
                                            </div>
                                          ),
                                          width: 700,
                                          okText: '关闭',
                                          className: 'glass-modal'
                                        });
                                      }}
                                    />
                                  </Tooltip>,
                                  <Tooltip title="删除" key="delete">
                                    <DeleteOutlined 
                                      style={{ color: '#ff4d4f', fontSize: '16px' }}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        Modal.confirm({
                                          title: '确认删除',
                                          content: '确定要删除这张图片吗？此操作不可恢复。',
                                          okText: '删除',
                                          cancelText: '取消',
                                          okType: 'danger',
                                          className: 'glass-modal',
                                          onOk: () => {
                                            console.log('删除图片:', img.filename);
                                            deleteHistoryImage(img.filename);
                                          }
                                        });
                                      }}
                                    />
                                  </Tooltip>
                                ]}
                              >
                                <div style={{ textAlign: 'center', position: 'relative' }}>
                                  {selectedHistoryImage === img.url && (
                                    <div style={{
                                      position: 'absolute',
                                      top: '4px',
                                      right: '4px',
                                      width: '20px',
                                      height: '20px',
                                      borderRadius: '50%',
                                      background: '#1890ff',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      zIndex: 2,
                                      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
                                    }}>
                                      <CheckOutlined style={{ fontSize: '12px', color: 'white' }} />
                                    </div>
                                  )}
                                  <Image
                                    src={img.url}
                                    alt={img.filename}
                                    width={80}
                                    height={60}
                                    style={{ 
                                      objectFit: 'cover',
                                      borderRadius: '4px',
                                      filter: selectedHistoryImage === img.url ? 'brightness(1.1)' : 'brightness(1)'
                                    }}
                                    preview={false}
                                  />
                                  <div style={{ 
                                    marginTop: '4px',
                                    fontSize: '10px',
                                    color: selectedHistoryImage === img.url ? '#1890ff' : 'rgba(255, 255, 255, 0.6)',
                                    textOverflow: 'ellipsis',
                                    overflow: 'hidden',
                                    whiteSpace: 'nowrap',
                                    fontWeight: selectedHistoryImage === img.url ? 'bold' : 'normal'
                                  }}>
                                    {formatFileSize(img.size)}
                                  </div>
                                  <div style={{ 
                                    fontSize: '9px',
                                    color: 'rgba(255, 255, 255, 0.5)',
                                    textOverflow: 'ellipsis',
                                    overflow: 'hidden',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {formatDate(img.uploaded_at)}
                                  </div>
                                </div>
                              </Card>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  }
                ]}
              />
            </div>
          )}
        </div>
      </Modal>
    </>
  );
};

export default ThemeSwitcher;

