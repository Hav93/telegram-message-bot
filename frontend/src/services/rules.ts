import { api } from './api';
import type {
  ForwardRule,
  CreateRuleDto,
  UpdateRuleDto,
  Keyword,
  CreateKeywordDto,
  ReplaceRule,
  CreateReplaceRuleDto,
} from '../types/rule';
// import type { PaginatedResponse } from '../types/api';

// 转发规则API
export const rulesApi = {
  // 获取规则列表
  list: async (): Promise<ForwardRule[]> => {
    try {
      const response: any = await api.get('/api/rules');
      return response.rules || [];
    } catch (error) {
      console.error('获取规则列表失败:', error);
      return [];
    }
  },

  // 获取单个规则
  get: async (id: number): Promise<ForwardRule> => {
    try {
      const response: any = await api.get(`/api/rules/${id}`);
      console.log('获取规则详情响应:', response);
      return response.rule;
    } catch (error) {
      console.error('获取规则详情失败:', error);
      throw error;
    }
  },

  // 创建规则
  create: async (data: CreateRuleDto): Promise<ForwardRule> => {
    try {
      const response: any = await api.post('/api/rules', data);
      return response.rule;
    } catch (error) {
      console.error('创建规则失败:', error);
      throw error;
    }
  },

  // 更新规则
  update: async (id: number, data: UpdateRuleDto): Promise<void> => {
    try {
      await api.put(`/api/rules/${id}`, data);
    } catch (error) {
      console.error('更新规则失败:', error);
      throw error;
    }
  },

  // 删除规则
  delete: async (id: number): Promise<void> => {
    try {
      console.log('正在删除规则:', id);
      const response = await api.delete(`/api/rules/${id}`);
      console.log('删除规则响应:', response);
    } catch (error) {
      console.error('删除规则失败:', error);
      throw error;
    }
  },

  // 切换规则状态
  toggle: async (id: number, enabled: boolean): Promise<any> => {
    return api.put(`/api/rules/${id}`, { is_active: enabled });
  },

  // 切换规则功能
  toggleFeature: async (id: number, feature: string, enabled: boolean): Promise<void> => {
    return api.put<void>(`/api/rules/${id}`, {
      [feature]: enabled,
    });
  },

  // 批量删除规则
  batchDelete: async (ids: number[]): Promise<void> => {
    // 暂时使用单个删除的方式实现批量删除
    for (const id of ids) {
      await api.delete<void>(`/api/rules/${id}`);
    }
  },

  // 导出规则
  export: async (ids?: number[]): Promise<any> => {
    const response = await api.post('/api/rules/export', { ids: ids || [] });
    return response;
  },

  // 导入规则
  import: async (data: any): Promise<any> => {
    const response = await api.post('/api/rules/import', { data });
    return response;
  },
};

// 关键词API
export const keywordsApi = {
  // 获取规则的关键词列表
  getByRule: async (ruleId: number): Promise<Keyword[]> => {
    try {
      const response: any = await api.get(`/api/rules/${ruleId}/keywords`);
      return response.keywords || [];
    } catch (error) {
      console.error('获取关键词列表失败:', error);
      return [];
    }
  },

  // 创建关键词
  create: async (data: CreateKeywordDto): Promise<Keyword> => {
    return api.post<Keyword>(`/api/rules/${data.rule_id}/keywords`, data);
  },

  // 更新关键词
  update: async (id: number, data: Partial<CreateKeywordDto>): Promise<Keyword> => {
    return api.put<Keyword>(`/api/keywords/${id}`, data);
  },

  // 删除关键词
  delete: async (id: number): Promise<void> => {
    return api.delete<void>(`/api/keywords/${id}`);
  },

  // 批量创建关键词
  batchCreate: async (ruleId: number, keywords: string[]): Promise<Keyword[]> => {
    return api.post<Keyword[]>(`/api/rules/${ruleId}/keywords/batch`, {
      keywords,
    });
  },
};

// 替换规则API
export const replaceRulesApi = {
  // 获取规则的替换规则列表
  getByRule: async (ruleId: number): Promise<ReplaceRule[]> => {
    try {
      const response: any = await api.get(`/api/rules/${ruleId}/replacements`);
      return response.replacements || [];
    } catch (error) {
      console.error('获取替换规则列表失败:', error);
      return [];
    }
  },

  // 创建替换规则
  create: async (data: CreateReplaceRuleDto): Promise<ReplaceRule> => {
    return api.post<ReplaceRule>(`/api/rules/${data.rule_id}/replacements`, data);
  },

  // 更新替换规则
  update: async (id: number, data: Partial<CreateReplaceRuleDto>): Promise<ReplaceRule> => {
    return api.put<ReplaceRule>(`/api/replacements/${id}`, data);
  },

  // 删除替换规则
  delete: async (id: number): Promise<void> => {
    return api.delete<void>(`/api/replacements/${id}`);
  },

  // 切换替换规则状态
  toggle: async (id: number, enabled: boolean): Promise<void> => {
    return api.patch<void>(`/api/replacements/${id}`, { is_active: enabled });
  },
};
