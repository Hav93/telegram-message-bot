import { api } from './api';
import type { ClientsResponse } from '../types/rule';

export const clientsApi = {
  // 获取所有客户端
  getClients: async (): Promise<ClientsResponse> => {
    const response = await api.get('/api/clients') as any;
    return response;
  },

  // 启动客户端
  startClient: async (clientId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/api/clients/${clientId}/start`) as any;
    return response;
  },

  // 停止客户端
  stopClient: async (clientId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/api/clients/${clientId}/stop`) as any;
    return response;
  },

  // 添加客户端
  addClient: async (data: { 
    client_id: string; 
    client_type: 'user' | 'bot';
    // 机器人客户端字段
    bot_token?: string;
    admin_user_id?: string;
    // 用户客户端字段
    api_id?: string;
    api_hash?: string;
    phone?: string;
  }): Promise<{ 
    success: boolean; 
    message: string;
    need_verification?: boolean;
    client_id?: string;
  }> => {
    const response = await api.post('/api/clients', data) as any;
    return response;
  },

  // 删除客户端
  removeClient: async (clientId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/api/clients/${clientId}`) as any;
    return response;
  },

  // 获取增强版系统状态
  getEnhancedStatus: async (): Promise<{
    success: boolean;
    enhanced_mode: boolean;
    clients?: Record<string, any>;
    total_clients?: number;
    running_clients?: number;
    connected_clients?: number;
    message?: string;
  }> => {
    const response = await api.get('/api/system/enhanced-status') as any;
    return response;
  },

  // 客户端登录流程
  clientLogin: async (clientId: string, loginData: {
    step: 'send_code' | 'submit_code' | 'submit_password';
    code?: string;
    password?: string;
  }): Promise<{
    success: boolean;
    message: string;
    step?: 'waiting_code' | 'waiting_password' | 'completed';
    user_info?: any;
  }> => {
    const response = await api.post(`/api/clients/${clientId}/login`, loginData) as any;
    return response; // 直接返回response，因为api.post已经返回了response.data
  },
};
