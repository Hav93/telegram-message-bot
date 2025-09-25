import { api } from './api.ts';

export interface BotSettings {
  api_id: string;
  api_hash: string;
  bot_token: string;
  phone_number: string;
  admin_user_ids: string;
  session_name?: string;
  enable_proxy: boolean;
  proxy_type: 'socks5' | 'socks4' | 'http';
  proxy_host: string;
  proxy_port: number;
  proxy_username?: string;
  proxy_password?: string;
  log_level: string;
  enable_log_cleanup: boolean;
  log_retention_days: number;
  log_cleanup_time: string;
  max_log_size: number;
}

export interface ProxyTestRequest {
  type: 'socks5' | 'socks4' | 'http';
  host: string;
  port: number;
  username?: string;
  password?: string;
}

export interface ProxyTestResponse {
  success: boolean;
  message: string;
  details?: {
    latency?: number;
    external_ip?: string;
    proxy_info?: {
      type: string;
      host: string;
      port: number;
      auth: boolean;
    };
  };
}

export interface TelegramLoginRequest {
  step: 'send_code' | 'submit_code' | 'submit_password' | 'reset';
  api_id?: string;
  api_hash?: string;
  phone_number?: string;
  code?: string;
  password?: string;
}

export interface TelegramLoginResponse {
  success: boolean;
  message: string;
  step?: 'password_required' | 'completed';
  error?: string;
}

export interface TelegramCredentialsTest {
  api_id: string;
  api_hash: string;
  phone_number: string;
}

export interface TelegramCredentialsResponse {
  success: boolean;
  valid: boolean;
  message: string;
  user?: {
    name: string;
    phone: string;
  };
}

export interface ConfigResponse {
  success: boolean;
  config: BotSettings;
}

export const settingsApi = {
  // 获取当前配置
  getCurrentConfig: async (): Promise<BotSettings> => {
    const response: any = await api.get('/api/settings');
    return response.config;
  },

  // 保存设置
  saveSettings: async (settings: Partial<BotSettings>): Promise<{ success: boolean; message: string }> => {
    try {
      const response: any = await api.post('/api/settings', settings);
      return response;
    } catch (error) {
      console.error('保存设置失败:', error);
      throw error;
    }
  },

  // 测试代理
  testProxy: async (proxyConfig: ProxyTestRequest): Promise<ProxyTestResponse> => {
    const response: any = await api.post('/api/test-proxy', proxyConfig);
    return response;
  },

  // Telegram登录流程
  telegramLogin: async (request: TelegramLoginRequest): Promise<TelegramLoginResponse> => {
    const response: any = await api.post('/api/telegram/login', request);
    return response;
  },

  // Telegram退出登录
  telegramLogout: async (): Promise<{ success: boolean; message: string }> => {
    const response: any = await api.post('/api/telegram/logout');
    return response;
  },

  // 获取Telegram状态
  getTelegramStatus: async (): Promise<{
    success: boolean;
    logged_in: boolean;
    user?: {
      first_name: string;
      last_name?: string;
      username?: string;
      phone?: string;
    };
    error?: string;
  }> => {
    const response: any = await api.get('/api/telegram/status');
    return response;
  },

  // 测试API凭据
  testCredentials: async (credentials: TelegramCredentialsTest): Promise<TelegramCredentialsResponse> => {
    const response: any = await api.post('/api/telegram/test-credentials', credentials);
    return response;
  },

  // 重启Telegram客户端
  restartClient: async (): Promise<{ success: boolean; message: string }> => {
    const response: any = await api.post('/api/telegram/restart-client', {});
    return response;
  },

  // 重启机器人
  restartBot: async (): Promise<{ success: boolean; message: string }> => {
    const response: any = await api.post('/api/telegram/restart');
    return response;
  },

  // 强制重载配置
  forceReloadConfig: async (): Promise<{ success: boolean; message: string }> => {
    const response: any = await api.post('/api/config/force-reload');
    return response;
  },

  // 测试日志清理
  testLogCleanup: async (config: {
    log_cleanup_time: string;
    log_retention_days: number;
  }): Promise<{ success: boolean; message: string }> => {
    const response: any = await api.post('/api/test-log-cleanup', config);
    return response;
  },

  // 获取配置同步状态
  getConfigSyncStatus: async (): Promise<{
    success: boolean;
    synced: boolean;
    last_sync: string;
  }> => {
    const response: any = await api.get('/api/config/sync-status');
    return response;
  }
};
