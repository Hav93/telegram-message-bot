import { api } from './api';
import type { MessageLog, LogFilters } from '../types/rule';
import type { PaginatedResponse } from '../types/api';

// 消息日志API
export const logsApi = {
  // 获取日志列表（分页）
  list: async (filters?: LogFilters): Promise<PaginatedResponse<MessageLog>> => {
    try {
      const params = new URLSearchParams();
      if (filters?.page) params.set('page', filters.page.toString());
      if (filters?.limit) params.set('limit', filters.limit.toString());
      if (filters?.date) params.set('date', filters.date);
      if (filters?.start_date) params.set('start_date', filters.start_date);
      if (filters?.end_date) params.set('end_date', filters.end_date);
      if (filters?.rule_id) params.set('rule_id', filters.rule_id.toString());
      if (filters?.status) params.set('status', filters.status);
      
      const response: any = await api.get(`/api/logs?${params.toString()}`);
      const data = response;
      
      return {
        items: data.items || [],  // 修复：后端返回的是 items 而不是 logs
        total: data.total || 0,
        page: data.page || 1,
        pageSize: data.limit || 10,
        totalPages: data.pages || 0,
      };
    } catch (error) {
      console.error('获取日志列表失败:', error);
      return {
        items: [],
        total: 0,
        page: 1,
        pageSize: 10,
        totalPages: 0,
      };
    }
  },

  // 获取单个日志详情
  get: async (id: number): Promise<MessageLog> => {
    return api.get<MessageLog>(`/api/logs/${id}`);
  },

  // 批量删除日志
  batchDelete: async (ids: number[]): Promise<void> => {
    console.log('logsApi.batchDelete 被调用，参数:', { ids });
    const response = await api.post<void>('/api/logs/batch-delete', { ids });
    console.log('logsApi.batchDelete 响应:', response);
    return response;
  },

  // 清空日志
  clear: async (filters?: LogFilters): Promise<void> => {
    return api.post<void>('/api/logs/clear', filters);
  },

  // 导出日志
  export: async (filters?: LogFilters): Promise<Blob> => {
    const response = await api.post('/api/logs/export', filters);
    return response as unknown as Blob;
  },

  // 导入日志
  import: async (formData: FormData): Promise<any> => {
    return api.post('/api/logs/import', formData);
  },

  // 获取日志统计
  stats: async (filters?: LogFilters): Promise<{
    total: number;
    success: number;
    failed: number;
    filtered: number;
    success_rate: number;
  }> => {
    return api.get('/api/logs/stats', filters);
  },

  // 获取消息类型统计
  messageTypeStats: async (filters?: LogFilters): Promise<Record<string, number>> => {
    return api.get('/api/logs/message-type-stats', filters);
  },

  // 获取规则统计
  ruleStats: async (filters?: LogFilters): Promise<Array<{
    rule_id: number;
    rule_name: string;
    total: number;
    success: number;
    failed: number;
    filtered: number;
  }>> => {
    return api.get('/api/logs/rule-stats', filters);
  },
};
