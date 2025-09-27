import { useState, useEffect } from 'react';

export type ThemeType = 'gradient' | 'dark' | 'gray' | 'custom';

export interface ThemeConfig {
  type: ThemeType;
  customImageUrl?: string;
}

const THEME_STORAGE_KEY = 'telegram-bot-theme';

const defaultThemes = {
  gradient: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    name: '紫蓝渐变'
  },
  dark: {
    background: '#1a1a1a',
    name: '深色主题'
  },
  gray: {
    background: 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
    name: '灰色主题'
  },
  custom: {
    background: '',
    name: '自定义背景'
  }
};

export const useTheme = () => {
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>(() => {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      return saved ? JSON.parse(saved) : { type: 'gradient' };
    } catch {
      return { type: 'gradient' };
    }
  });

  const [currentBackground, setCurrentBackground] = useState<string>('');

  useEffect(() => {
    let background = '';
    
    if (themeConfig.type === 'custom' && themeConfig.customImageUrl) {
      background = `url("${themeConfig.customImageUrl}")`;
      console.log('🎨 应用自定义背景:', themeConfig.customImageUrl);
    } else {
      background = defaultThemes[themeConfig.type].background;
      console.log('🎨 应用预设主题:', themeConfig.type, background);
    }
    
    setCurrentBackground(background);
    
    // 应用背景到 document.body
    const body = document.body;
    const root = document.getElementById('root');
    
    // 移除之前的主题类名
    body.classList.remove('theme-gradient', 'theme-dark', 'theme-gray', 'theme-custom');
    
    // 添加当前主题类名
    body.classList.add(`theme-${themeConfig.type}`);
    
    if (themeConfig.type === 'custom' && themeConfig.customImageUrl) {
      const customBg = `url("${themeConfig.customImageUrl}") center center / cover no-repeat fixed`;
      body.style.background = customBg;
      body.style.backgroundSize = 'cover';
      body.style.backgroundPosition = 'center center';
      body.style.backgroundRepeat = 'no-repeat';
      body.style.backgroundAttachment = 'fixed';
      
      if (root) {
        root.style.background = customBg;
        root.style.backgroundSize = 'cover';
        root.style.backgroundPosition = 'center center';
        root.style.backgroundRepeat = 'no-repeat';
        root.style.backgroundAttachment = 'fixed';
      }
      
      console.log('✅ 自定义背景样式已应用:', customBg);
    } else {
      body.style.background = background;
      body.style.backgroundAttachment = 'fixed';
      body.style.backgroundSize = '';
      body.style.backgroundPosition = '';
      body.style.backgroundRepeat = '';
      
      if (root) {
        root.style.background = background;
        root.style.backgroundAttachment = 'fixed';
        root.style.backgroundSize = '';
        root.style.backgroundPosition = '';
        root.style.backgroundRepeat = '';
      }
      
      console.log('✅ 预设主题样式已应用');
    }
    
    // 保存到 localStorage
    try {
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(themeConfig));
    } catch (error) {
      console.warn('无法保存主题配置到 localStorage:', error);
    }
  }, [themeConfig]);

  const changeTheme = (type: ThemeType, customImageUrl?: string) => {
    setThemeConfig({
      type,
      customImageUrl: type === 'custom' ? customImageUrl : undefined
    });
  };

  const getThemeName = () => {
    if (themeConfig.type === 'custom') {
      return themeConfig.customImageUrl ? '自定义背景' : '自定义背景 (未设置)';
    }
    return defaultThemes[themeConfig.type].name;
  };

  return {
    themeConfig,
    currentBackground,
    changeTheme,
    getThemeName,
    defaultThemes
  };
};

