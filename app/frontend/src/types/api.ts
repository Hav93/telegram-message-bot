// API响应和请求类型定义

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 聊天类型
export interface Chat {
  id: string;
  name: string;
  title?: string;
  first_name?: string;
  type: 'private' | 'group' | 'supergroup' | 'channel' | 'user';
  username?: string;
  photo?: string;
  description?: string;
  members_count?: number;
  is_active?: boolean;
  last_activity?: string;
  invite_link?: string;
  client_id: string;
  client_type: 'user' | 'bot';
  client_display_name?: string;
  is_verified?: boolean;
  is_scam?: boolean;
  is_fake?: boolean;
  unread_count?: number;
  last_message_date?: string;
}

export interface ClientInfo {
  client_id: string;
  client_type: 'user' | 'bot';
  chat_count: number;
  display_name: string;
}

export interface ChatsResponse {
  chats: Chat[];
  chats_by_client: Record<string, Chat[]>;
  clients_info: ClientInfo[];
  total_chats: number;
  connected_clients: number;
  last_updated?: string;
}

// 系统状态
export interface SystemStatus {
  success: boolean;
  logged_in: boolean;
  message?: string;
  config_complete?: boolean;
  bot_running?: boolean;
  user?: {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
    phone?: string;
    is_bot: boolean;
    is_verified?: boolean;
    is_premium?: boolean;
  };
  error?: string;
}

// 统计数据
export interface Stats {
  today_messages: number;
  success_messages: number;
  success_rate: number;
  week_stats: Array<{
    date: string;
    count: number;
  }>;
}

// 配置相关
export interface TelegramConfig {
  api_id?: string;
  api_hash?: string;
  bot_token?: string;
  phone_number?: string;
}

export interface ProxyConfig {
  enable_proxy: boolean;
  proxy_type: 'http' | 'socks5';
  proxy_host: string;
  proxy_port: number;
  proxy_username?: string;
  proxy_password?: string;
}

export interface BotSettings {
  id?: number;
  key: string;
  value: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}
