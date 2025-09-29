import React, { useState, useEffect } from 'react';
import { Modal, Slider, Switch, Button, Space, Typography, ColorPicker, Collapse } from 'antd';
import { SettingOutlined, DownOutlined } from '@ant-design/icons';
import type { Color } from 'antd/es/color-picker';

const { Text } = Typography;

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

const defaultSettings: GlassSettings = {
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

// DEBUG: Force build change - this should appear in built files
const BUILD_VERSION = 'FINAL-BUILD-2024-12-19-TEST';

// Add a global variable to window to ensure it's not tree-shaken
if (typeof window !== 'undefined') {
  (window as any).BUILD_VERSION_GLASS_SETTINGS = BUILD_VERSION;
  // Add a unique string that should survive minification
  console.log('🚀 GlassSettings loaded - BUILD_VERSION_FINAL_2024_12_19_TEST');
}

const textureOptions = [
  { value: 'rice-paper', label: 'Rice Paper', url: 'https://www.transparenttextures.com/patterns/rice-paper.png' },
  { value: 'egg-shell', label: 'Egg Shell', url: 'https://www.transparenttextures.com/patterns/egg-shell.png' },
  { value: 'ink-jet', label: 'Ink Jet', url: 'https://www.transparenttextures.com/patterns/ink-jet.png' },
  { value: 'coarse', label: 'Coarse', url: 'https://www.transparenttextures.com/patterns/coarse.png' },
  { value: 'topology', label: 'Topology', url: 'https://www.transparenttextures.com/patterns/topology.png' }
];

const GlassSettings: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [settings, setSettings] = useState<GlassSettings>(() => {
    try {
      const saved = localStorage.getItem('glass-settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        console.log('📊 加载已保存的玻璃质感设置:', parsed);
        return { ...defaultSettings, ...parsed }; // 合并默认设置，避免缺失字段
      }
    } catch (error) {
      console.error('📊 加载玻璃质感设置失败:', error);
      localStorage.removeItem('glass-settings'); // 清除损坏的数据
    }
    console.log('📊 使用默认玻璃质感设置:', defaultSettings);
    return defaultSettings;
  });

  // 应用设置到CSS变量
  const applySettings = (newSettings: GlassSettings) => {
    const root = document.documentElement;
    
    console.log('🎨 应用玻璃质感设置:', newSettings);
    
    if (newSettings.enabled) {
      const { h, s, l, a } = newSettings.color;
      const textureUrl = textureOptions.find(t => t.value === newSettings.texture)?.url || '';
      
      const glassFilter = `blur(${newSettings.blur}px) brightness(${newSettings.brightness}) saturate(${newSettings.saturation})`;
      const glassColor = `hsl(${h} ${s}% ${l}% / ${a})`;
      const glassTexture = textureUrl ? `url("${textureUrl}")` : 'none';
      
      console.log('🎨 设置CSS变量:', {
        '--glass-filter': glassFilter,
        '--glass-color': glassColor,
        '--glass-texture': glassTexture
      });
      
      root.style.setProperty('--glass-filter', glassFilter);
      root.style.setProperty('--glass-color', glassColor);
      root.style.setProperty('--glass-texture', glassTexture);
      
      // 验证CSS变量是否设置成功
      setTimeout(() => {
        const actualFilter = getComputedStyle(root).getPropertyValue('--glass-filter');
        const actualColor = getComputedStyle(root).getPropertyValue('--glass-color');
        console.log('🎨 验证CSS变量设置结果:', {
          expected: { filter: glassFilter, color: glassColor },
          actual: { filter: actualFilter, color: actualColor }
        });
      }, 100);
    } else {
      root.style.setProperty('--glass-filter', 'none');
      root.style.setProperty('--glass-color', 'rgba(255, 255, 255, 0.06)');
      root.style.setProperty('--glass-texture', 'none');
      console.log('🎨 玻璃质感已禁用，使用默认设置');
    }
  };

  // 初始化应用设置
  useEffect(() => {
    console.log('📊 初始化玻璃质感设置:', settings);
    applySettings(settings);
    
    // 验证localStorage中的设置是否与当前设置一致
    try {
      const saved = localStorage.getItem('glass-settings');
      if (saved) {
        const savedSettings = JSON.parse(saved);
        const isConsistent = JSON.stringify(savedSettings) === JSON.stringify(settings);
        if (!isConsistent) {
          console.log('📊 检测到设置不一致，重新保存当前设置');
          localStorage.setItem('glass-settings', JSON.stringify(settings));
        }
      } else {
        console.log('📊 localStorage中无设置，保存当前设置');
        localStorage.setItem('glass-settings', JSON.stringify(settings));
      }
    } catch (error) {
      console.error('📊 初始化设置验证失败:', error);
    }
  }, []);
  
  // 监听settings变化，确保实时同步
  useEffect(() => {
    applySettings(settings);
  }, [settings]);

  // 更新设置
  const updateSettings = (newSettings: Partial<GlassSettings>) => {
    try {
      const updated = { ...settings, ...newSettings };
      console.log('📊 更新玻璃质感设置:', { old: settings, new: newSettings, updated });
      
      setSettings(updated);
      applySettings(updated);
      
      // 保存到localStorage
      localStorage.setItem('glass-settings', JSON.stringify(updated));
      console.log('📊 玻璃质感设置已保存到localStorage');
      
      // 验证保存是否成功
      const saved = localStorage.getItem('glass-settings');
      if (saved) {
        const verified = JSON.parse(saved);
        console.log('📊 验证保存的设置:', verified);
      }
    } catch (error) {
      console.error('📊 保存玻璃质感设置失败:', error);
      // 即使保存失败，也要应用设置到当前会话
      const updated = { ...settings, ...newSettings };
      setSettings(updated);
      applySettings(updated);
    }
  };

  // 重置为默认设置
  const resetSettings = () => {
    try {
      console.log('📊 重置玻璃质感设置为默认值:', defaultSettings);
      setSettings(defaultSettings);
      applySettings(defaultSettings);
      localStorage.setItem('glass-settings', JSON.stringify(defaultSettings));
      console.log('📊 默认设置已保存到localStorage');
    } catch (error) {
      console.error('📊 重置设置失败:', error);
      // 即使保存失败，也要应用默认设置到当前会话
      setSettings(defaultSettings);
      applySettings(defaultSettings);
    }
  };

  // 颜色选择器变化
  const handleColorChange = (color: Color) => {
    console.log('🚀 Build version:', BUILD_VERSION);
    console.log('🚀 NEW CODE VERSION 2024-12-19-FINAL - ColorPicker onChange triggered');
    console.log('Available methods:', Object.getOwnPropertyNames(color));
    
    // 尝试多种方法获取颜色值
    try {
      const hsb = color.toHsb();
      console.log('HSB values:', hsb);
      
      // 尝试使用hex转换
      const hex = color.toHex();
      console.log('HEX value:', hex);
      
      // 手动从hex计算HSL
      const hexToHsl = (hex: string) => {
        // 移除#号
        const cleanHex = hex.replace('#', '');
        const r = parseInt(cleanHex.substr(0, 2), 16) / 255;
        const g = parseInt(cleanHex.substr(2, 2), 16) / 255;
        const b = parseInt(cleanHex.substr(4, 2), 16) / 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h = 0;
        let s = 0;
        const l = (max + min) / 2;
        
        if (max !== min) {
          const d = max - min;
          s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
          
          switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
          }
          h /= 6;
        }
        
        return {
          h: Math.round(h * 360),
          s: Math.round(s * 100),
          l: Math.round(l * 100)
        };
      };
      
      const hslFromHex = hexToHsl(hex);
      console.log('HSL calculated from HEX:', hslFromHex);
      
      const a = Number((hsb.a || 1).toFixed(2));
      
      const cssValue = `hsl(${hslFromHex.h} ${hslFromHex.s}% ${hslFromHex.l}% / ${a})`;
      console.log('Final CSS value:', cssValue);
      
      updateSettings({
        color: { 
          h: hslFromHex.h, 
          s: hslFromHex.s, 
          l: hslFromHex.l, 
          a 
        }
      });
      
    } catch (error) {
      console.error('Color conversion error:', error);
    }
  };

  // 导出设置
  const exportSettings = () => {
    try {
      const dataStr = JSON.stringify(settings, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = 'glass-settings.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      console.log('📊 设置已导出');
    } catch (error) {
      console.error('📊 导出设置失败:', error);
    }
  };

  // 导入设置
  const importSettings = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target?.result as string);
        const merged = { ...defaultSettings, ...imported };
        setSettings(merged);
        applySettings(merged);
        localStorage.setItem('glass-settings', JSON.stringify(merged));
        console.log('📊 设置已导入:', merged);
      } catch (error) {
        console.error('📊 导入设置失败:', error);
      }
    };
    reader.readAsText(file);
    
    // 重置input value，允许重复导入同一文件
    event.target.value = '';
  };

  return (
    <>
      {/* 触发按钮 */}
      <Button
        type="text"
        icon={<SettingOutlined />}
        onClick={() => setVisible(true)}
        style={{
          color: 'rgba(255, 255, 255, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(4px)'
        }}
      >
        玻璃质感设置
      </Button>

      {/* 设置面板 */}
      <Modal
        title={
          <Space>
            <SettingOutlined />
            <span style={{ color: '#ffffff' }}>玻璃质感设置</span>
          </Space>
        }
        open={visible}
        onCancel={() => setVisible(false)}
        className="glass-modal"
        width={450}
        styles={{
          content: {
            background: 'transparent',
            padding: 0
          },
          body: {
            background: 'transparent',
            padding: '16px 24px',
            maxHeight: '480px',
            overflowY: 'auto'
          },
          footer: {
            background: 'transparent',
            borderTop: 'none'
          }
        }}
        footer={[
          <Button key="export" onClick={exportSettings}>
            导出设置
          </Button>,
          <label key="import" style={{ display: 'inline-block' }}>
            <input
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={importSettings}
            />
            <Button>
              导入设置
            </Button>
          </label>,
          <Button key="reset" onClick={resetSettings}>
            重置默认
          </Button>,
          <Button key="close" type="primary" onClick={() => setVisible(false)}>
            完成
          </Button>
        ]}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          
          {/* 主开关 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Text strong style={{ color: '#ffffff', fontSize: '16px' }}>启用玻璃质感效果</Text>
              <Switch
                checked={settings.enabled}
                onChange={(enabled) => updateSettings({ enabled })}
                size="default"
              />
            </div>
          </div>

          {settings.enabled && (
            <Collapse
              ghost
              expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} style={{ color: '#ffffff' }} />}
              style={{ 
                background: 'transparent',
                border: 'none'
              }}
              items={[
                {
                  key: 'backdrop-filter',
                  label: (
                    <Text strong style={{ color: '#ffffff', fontSize: '15px' }}>
                      backdrop-filter 滤镜效果
                    </Text>
                  ),
                  children: (
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                      {/* 模糊度 */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.9)' }}>✓ blur 模糊</Text>
                          <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{settings.blur}px</Text>
                        </div>
                        <Slider
                          min={0}
                          max={20}
                          step={1}
                          value={settings.blur}
                          onChange={(blur) => updateSettings({ blur })}
                          trackStyle={{ backgroundColor: '#1890ff' }}
                          handleStyle={{ borderColor: '#1890ff' }}
                        />
                      </div>

                      {/* 亮度 */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.9)' }}>✓ brightness 亮度</Text>
                          <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{settings.brightness}</Text>
                        </div>
                        <Slider
                          min={0}
                          max={2}
                          step={0.1}
                          value={settings.brightness}
                          onChange={(brightness) => updateSettings({ brightness })}
                          trackStyle={{ backgroundColor: '#1890ff' }}
                          handleStyle={{ borderColor: '#1890ff' }}
                        />
                      </div>

                      {/* 饱和度 */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.9)' }}>✓ saturation 饱和度</Text>
                          <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{settings.saturation}</Text>
                        </div>
                        <Slider
                          min={0}
                          max={2}
                          step={0.1}
                          value={settings.saturation}
                          onChange={(saturation) => updateSettings({ saturation })}
                          trackStyle={{ backgroundColor: '#1890ff' }}
                          handleStyle={{ borderColor: '#1890ff' }}
                        />
                      </div>
                    </Space>
                  )
                },
                {
                  key: 'color',
                  label: (
                    <Text strong style={{ color: '#ffffff', fontSize: '15px' }}>
                      color 背景颜色 [UPDATED-FINAL]
                    </Text>
                  ),
                  children: (
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                
                      {/* HSL颜色选择器 */}
                      <div style={{ marginBottom: 16 }}>
                        <ColorPicker
                          value={`hsl(${settings.color.h}, ${settings.color.s}%, ${settings.color.l}%, ${settings.color.a})`}
                          onChange={handleColorChange}
                          showText={(_color) => (
                            <span style={{ color: '#ffffff' }}>
                              hsl({settings.color.h} {settings.color.s}% {settings.color.l}% / {settings.color.a})
                            </span>
                          )}
                          size="large"
                        />
                      </div>

                      {/* 透明度单独调节 */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <Text style={{ color: 'rgba(255, 255, 255, 0.9)' }}>透明度</Text>
                          <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{settings.color.a}</Text>
                        </div>
                        <Slider
                          min={0}
                          max={1}
                          step={0.01}
                          value={settings.color.a}
                          onChange={(a) => updateSettings({ 
                            color: { ...settings.color, a } 
                          })}
                          trackStyle={{ backgroundColor: '#1890ff' }}
                          handleStyle={{ borderColor: '#1890ff' }}
                        />
                      </div>
                    </Space>
                  )
                },
                {
                  key: 'texture',
                  label: (
                    <Text strong style={{ color: '#ffffff', fontSize: '15px' }}>
                      texture 纹理效果
                    </Text>
                  ),
                  children: (
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      {textureOptions.map((option) => (
                        <div
                          key={option.value}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            background: settings.texture === option.value 
                              ? 'rgba(24, 144, 255, 0.2)' 
                              : 'rgba(255, 255, 255, 0.05)',
                            border: settings.texture === option.value 
                              ? '1px solid #1890ff' 
                              : '1px solid rgba(255, 255, 255, 0.1)',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease'
                          }}
                          onClick={() => updateSettings({ texture: option.value as any })}
                        >
                          <div
                            style={{
                              width: '8px',
                              height: '8px',
                              borderRadius: '50%',
                              background: settings.texture === option.value ? '#1890ff' : 'rgba(255, 255, 255, 0.3)',
                              marginRight: '8px'
                            }}
                          />
                          <Text style={{ color: '#ffffff' }}>{option.label}</Text>
                        </div>
                      ))}
                    </Space>
                  )
                }
              ]}
              defaultActiveKey={['backdrop-filter']}
            />
          )}
        </Space>
      </Modal>
    </>
  );
};

export default GlassSettings;
