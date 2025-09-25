import { api } from './api.ts';
import type { Chat, ChatsResponse } from '../types/api.ts';

export interface ChatGroups {
  [key: string]: Chat[];
}

export interface RefreshChatsResponse {
  success: boolean;
  message: string;
  updated_count: number;
}

export const chatsApi = {
  // 获取聊天列表
  getChats: async (): Promise<ChatsResponse> => {
    const response: any = await api.get('/api/chats');
    return response;
  },

  // 刷新聊天列表
  refreshChats: async (): Promise<RefreshChatsResponse> => {
    const response: any = await api.post('/api/refresh-chats');
    return response;
  },

  // 导出聊天列表
  export: async (): Promise<Blob> => {
    const response = await api.post('/api/chats/export', {});
    return response as unknown as Blob;
  },

  // 导入聊天列表
  import: async (formData: FormData): Promise<any> => {
    return api.post('/api/chats/import', formData);
  },

  // 搜索聊天
  searchChats: (chats: Chat[], searchTerm: string): Chat[] => {
    if (!searchTerm.trim()) return chats;
    
    const term = searchTerm.toLowerCase();
    return chats.filter(chat => 
      (chat.title || '').toLowerCase().includes(term) ||
      chat.id.includes(term) ||
      (chat.username && chat.username.toLowerCase().includes(term)) ||
      (chat.description && chat.description.toLowerCase().includes(term))
    );
  },

  // 按类型筛选聊天
  filterChatsByType: (chats: Chat[], type?: string): Chat[] => {
    if (!type) return chats;
    return chats.filter(chat => chat.type === type);
  },

  // 排序聊天
  sortChats: (chats: Chat[], sortBy: 'name' | 'type' | 'id'): Chat[] => {
    return [...chats].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.title || '').localeCompare(b.title || '');
        case 'type':
          return a.type.localeCompare(b.type);
        case 'id':
          return parseInt(a.id) - parseInt(b.id);
        default:
          return 0;
      }
    });
  },

  // 将聊天分组
  groupChats: (chats: Chat[]): ChatGroups => {
    const groups: ChatGroups = {};
    
    chats.forEach(chat => {
      if (!groups[chat.type]) {
        groups[chat.type] = [];
      }
      groups[chat.type].push(chat);
    });

    return groups;
  },

  // 导出聊天数据
  exportChats: (chats: Chat[]): void => {
    const chatData = chats.map(chat => ({
      id: chat.id,
      name: chat.title || chat.first_name || 'Unknown',
      type: chat.type,
      username: chat.username || '',
      description: chat.description || '',
      member_count: chat.members_count || 0
    }));

    const blob = new Blob([JSON.stringify(chatData, null, 2)], { 
      type: 'application/json' 
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `telegram_chats_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  // 复制到剪贴板
  copyToClipboard: async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.error('复制失败:', err);
      return false;
    }
  },

  // 生成创建规则的URL
  generateCreateRuleUrl: (chatId: string, chatTitle: string): string => {
    const params = new URLSearchParams({
      source_chat_id: chatId,
      source_chat_name: chatTitle
    });
    return `/rules/new?${params.toString()}`;
  }
};
