import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
// import type { ApiResponse, PaginatedResponse } from '../types/api';

// 创建axios实例 - 简化版（参考v3.1）
const createApiClient = (): AxiosInstance => {
  // 在生产环境中，API和前端在同一个容器内，使用相对路径
  // 在开发环境中，使用localhost
  const baseURL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:9393');
  
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // 支持跨域cookie
  });

  // 请求拦截器 - 简化版
  client.interceptors.request.use(
    (config) => {
      // 添加时间戳防止缓存
      if (config.method === 'get') {
        config.params = {
          ...config.params,
          _t: Date.now(),
        };
      }
      
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
      return config;
    },
    (error) => {
      console.error('[API] Request error:', error);
      return Promise.reject(error);
    }
  );

  // 响应拦截器 - 简化版
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      console.log(`[API] Response ${response.status}:`, response.data);
      return response;
    },
    (error) => {
      console.error('[API] Response error:', error.response?.data || error.message);
      
      // 处理特定HTTP状态码
      if (error.response?.status === 401) {
        // 未授权，可能需要重新登录
        console.warn('未授权访问，建议检查登录状态');
      } else if (error.response?.status === 403) {
        // 禁止访问
        console.error('访问被禁止');
      } else if (error.response?.status >= 500) {
        // 服务器错误
        console.error('服务器内部错误');
      }
      
      return Promise.reject(error);
    }
  );

  return client;
};

export const apiClient = createApiClient();

// 通用API响应处理函数
export const handleApiResponse = <T>(response: AxiosResponse<T>): T => {
  return response.data;
};

export const handleApiError = (error: any): never => {
  const message = error.response?.data?.message || error.message || '请求失败';
  throw new Error(message);
};

// 封装常用HTTP方法
export const api = {
  get: async <T>(url: string, params?: any): Promise<T> => {
    try {
      const response = await apiClient.get<T>(url, { params });
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error);
    }
  },

  post: async <T>(url: string, data?: any): Promise<T> => {
    try {
      const response = await apiClient.post<T>(url, data);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error);
    }
  },

  put: async <T>(url: string, data?: any): Promise<T> => {
    try {
      const response = await apiClient.put<T>(url, data);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error);
    }
  },

  patch: async <T>(url: string, data?: any): Promise<T> => {
    try {
      const response = await apiClient.patch<T>(url, data);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error);
    }
  },

  delete: async <T>(url: string): Promise<T> => {
    try {
      const response = await apiClient.delete<T>(url);
      return handleApiResponse(response);
    } catch (error) {
      return handleApiError(error);
    }
  },
};

export default api;
