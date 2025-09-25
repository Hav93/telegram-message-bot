import { api } from './api.ts';
import type {
  Chat,
  SystemStatus,
  Stats,
  TelegramConfig,
  ProxyConfig,
  BotSettings,
} from '../types/api.ts';

// 系统管理API
export const systemApi = {
  // 获取系统状态
  status: async (): Promise<SystemStatus> => {
    return api.get<SystemStatus>('/api/telegram/status');
  },

  // 获取统计数据
  stats: async (): Promise<Stats> => {
    return api.get<Stats>('/api/stats');
  },

  // 重启Telegram客户端
  restart: async (): Promise<void> => {
    return api.post<void>('/api/telegram/restart');
  },

  // 测试Telegram凭据
  testCredentials: async (config: TelegramConfig): Promise<{
    success: boolean;
    message: string;
  }> => {
    return api.post('/api/telegram/test-credentials', config);
  },

  // 获取当前配置
  getConfig: async (): Promise<any> => {
    return api.get('/api/config/current');
  },

  // 强制重新加载配置
  reloadConfig: async (): Promise<void> => {
    return api.post<void>('/api/config/force-reload');
  },

  // 获取配置同步状态
  getConfigSyncStatus: async (): Promise<{
    docker_env_sync: boolean;
    config_file_exists: boolean;
    last_sync: string;
  }> => {
    return api.get('/api/config/sync-status');
  },
};

// 聊天管理API
export const chatsApi = {
  // 获取聊天列表
  list: async (): Promise<{ chats: Chat[]; debug?: any }> => {
    return api.get<{ chats: Chat[]; debug?: any }>('/api/chats');
  },

  // 刷新聊天列表
  refresh: async (): Promise<{ chats: Chat[] }> => {
    return api.post<{ chats: Chat[] }>('/api/refresh-chats');
  },

  // 刷新监听器
  refreshListeners: async (): Promise<void> => {
    return api.post<void>('/api/refresh-listeners');
  },
};

// 代理管理API
export const proxyApi = {
  // 测试代理连接
  test: async (config: ProxyConfig): Promise<{
    success: boolean;
    message: string;
    details?: any;
  }> => {
    return api.post('/api/test-proxy', config);
  },
};

// 设置管理API
export const settingsApi = {
  // 获取所有设置
  list: async (): Promise<BotSettings[]> => {
    return api.get<BotSettings[]>('/api/settings');
  },

  // 获取单个设置
  get: async (key: string): Promise<BotSettings> => {
    return api.get<BotSettings>(`/api/settings/${key}`);
  },

  // 更新设置
  update: async (key: string, value: string): Promise<BotSettings> => {
    return api.put<BotSettings>(`/api/settings/${key}`, { value });
  },

  // 批量更新设置
  batchUpdate: async (settings: Record<string, string>): Promise<void> => {
    return api.post<void>('/api/settings/batch', settings);
  },

  // 重置设置
  reset: async (key: string): Promise<void> => {
    return api.delete<void>(`/api/settings/${key}`);
  },
};

// Telegram登录API
export const authApi = {
  // 发送验证码
  sendCode: async (config: {
    api_id: string;
    api_hash: string;
    phone_number: string;
  }): Promise<{
    success: boolean;
    step: string;
    message: string;
  }> => {
    return api.post('/api/telegram/login', {
      step: 'send_code',
      ...config,
    });
  },

  // 提交验证码
  submitCode: async (code: string): Promise<{
    success: boolean;
    step: string;
    message: string;
  }> => {
    return api.post('/api/telegram/login', {
      step: 'submit_code',
      code,
    });
  },

  // 提交密码（如果需要）
  submitPassword: async (password: string): Promise<{
    success: boolean;
    step: string;
    message: string;
  }> => {
    return api.post('/api/telegram/submit-password', {
      password,
    });
  },

  // 登出
  logout: async (): Promise<void> => {
    return api.post<void>('/api/telegram/logout');
  },

  // 重置登录状态
  reset: async (): Promise<void> => {
    return api.post<void>('/api/telegram/login', {
      step: 'reset',
    });
  },
};
