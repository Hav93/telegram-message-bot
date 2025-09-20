import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// 主题类型
export type Theme = 'light' | 'dark' | 'auto';

// 语言类型
export type Language = 'zh-CN' | 'en-US';

// 用户信息
export interface User {
  id: string;
  username?: string;
  phone_number?: string;
  is_admin: boolean;
}

// 应用状态
interface AppState {
  // 主题设置
  theme: Theme;
  setTheme: (theme: Theme) => void;
  
  // 语言设置
  language: Language;
  setLanguage: (language: Language) => void;
  
  // 侧边栏状态
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  
  // 用户信息
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  
  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;
  
  // 全局消息通知
  notification: {
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    description?: string;
  } | null;
  setNotification: (notification: AppState['notification']) => void;
  clearNotification: () => void;
  
  // 应用初始化状态
  initialized: boolean;
  setInitialized: (initialized: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // 初始状态
      theme: 'auto',
      language: 'zh-CN',
      sidebarCollapsed: false,
      currentUser: null,
      loading: false,
      notification: null,
      initialized: false,
      
      // 主题相关方法
      setTheme: (theme) => {
        set({ theme });
        // 应用主题到DOM
        applyTheme(theme);
      },
      
      // 语言相关方法
      setLanguage: (language) => {
        set({ language });
        // 可以在这里触发i18n语言切换
      },
      
      // 侧边栏相关方法
      setSidebarCollapsed: (collapsed) => {
        set({ sidebarCollapsed: collapsed });
      },
      
      // 用户相关方法
      setCurrentUser: (user) => {
        set({ currentUser: user });
      },
      
      // 加载状态方法
      setLoading: (loading) => {
        set({ loading });
      },
      
      // 通知相关方法
      setNotification: (notification) => {
        set({ notification });
      },
      
      clearNotification: () => {
        set({ notification: null });
      },
      
      // 初始化相关方法
      setInitialized: (initialized) => {
        set({ initialized });
      },
    }),
    {
      name: 'app-store', // 存储key
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只持久化这些字段
        theme: state.theme,
        language: state.language,
        sidebarCollapsed: state.sidebarCollapsed,
        currentUser: state.currentUser,
      }),
    }
  )
);

// 应用主题到DOM的辅助函数
const applyTheme = (theme: Theme) => {
  const root = document.documentElement;
  
  if (theme === 'auto') {
    // 自动模式：根据系统设置
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', isDark ? 'dark' : 'light');
  } else {
    root.setAttribute('data-theme', theme);
  }
};

// 监听系统主题变化
const watchSystemTheme = () => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  
  const handleChange = () => {
    const { theme } = useAppStore.getState();
    if (theme === 'auto') {
      applyTheme('auto');
    }
  };
  
  mediaQuery.addEventListener('change', handleChange);
  
  return () => {
    mediaQuery.removeEventListener('change', handleChange);
  };
};

// 初始化主题
export const initializeTheme = () => {
  const { theme } = useAppStore.getState();
  applyTheme(theme);
  
  // 监听系统主题变化
  return watchSystemTheme();
};
