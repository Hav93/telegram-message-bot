import { api } from './api';

export interface DashboardStats {
  total_rules: number;
  active_rules: number;
  today_messages: number;
  success_rate: number;
  success_messages: number;
}

export interface RecentRule {
  id: number;
  name: string;
  source_chat_name?: string;
  source_chat_id: string;
  target_chat_name?: string;
  target_chat_id: string;
  is_active: boolean;
  created_at: string;
}

export interface RecentLog {
  id: number;
  rule_id?: number;
  source_chat_name?: string;
  source_chat_id: string;
  target_chat_name?: string;
  target_chat_id: string;
  status: 'success' | 'failed' | 'pending' | 'processing' | 'skipped';
  processed_text?: string;
  original_text?: string;
  created_at: string;
}

export interface SystemStatus {
  bot_running: boolean;
  proxy_enabled: boolean;
  proxy_type?: string;
}

export interface TelegramStatus {
  logged_in: boolean;
  user?: {
    first_name: string;
    last_name?: string;
    username?: string;
    phone?: string;
  };
  error?: string;
}

export const dashboardApi = {
  // 获取统计数据
  getStats: async (): Promise<DashboardStats> => {
    const response: any = await api.get('/api/stats');
    return response;
  },

  // 获取Telegram状态
  getTelegramStatus: async (): Promise<TelegramStatus> => {
    const response: any = await api.get('/api/telegram/status');
    return response;
  },

  // 获取最近规则 (使用现有规则API的前几条)
  getRecentRules: async (_limit = 5): Promise<RecentRule[]> => {
    try {
      // 注意：这里可能需要后端恢复 GET /rules 接口
      console.warn('获取最近规则: 后端GET /rules接口被注释，返回空数据');
      return [];
    } catch (error) {
      console.error('获取最近规则失败:', error);
      return [];
    }
  },

  // 获取最近日志 (使用现有日志API的前几条)
  getRecentLogs: async (_limit = 10): Promise<RecentLog[]> => {
    try {
      // 注意：这里可能需要后端恢复 GET /logs 接口或者添加 GET /api/logs
      console.warn('获取最近日志: 后端GET /logs接口被注释，返回空数据');
      return [];
    } catch (error) {
      console.error('获取最近日志失败:', error);
      return [];
    }
  },

  // 刷新统计数据
  refreshStats: async (): Promise<DashboardStats> => {
    return dashboardApi.getStats();
  }
};
