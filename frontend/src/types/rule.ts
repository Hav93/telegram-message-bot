// 转发规则相关类型定义

export interface ForwardRule {
  id: number;
  name: string;
  source_chat_id: string;
  source_chat_name?: string;
  target_chat_id: string;
  target_chat_name?: string;
  
  // 功能开关
  is_active: boolean;
  enable_keyword_filter: boolean;
  enable_regex_replace: boolean;
  
  // 客户端选择
  client_id: string;
  client_type: 'user' | 'bot';
  
  // 消息类型支持
  enable_text: boolean;
  enable_media: boolean;
  enable_photo: boolean;
  enable_video: boolean;
  enable_document: boolean;
  enable_audio: boolean;
  enable_voice: boolean;
  enable_sticker: boolean;
  enable_animation: boolean;
  enable_webpage: boolean;
  
  // 高级设置
  forward_delay: number;
  max_message_length: number;
  enable_link_preview: boolean;
  
  // 时间过滤设置
  time_filter_type: 'after_start' | 'all_messages' | 'today_only' | 'from_time' | 'time_range';
  start_time?: string;
  end_time?: string;
  
  // 时间戳
  created_at: string;
  updated_at: string;
  
  // 关联数据
  keywords?: Keyword[];
  replace_rules?: ReplaceRule[];
  message_logs?: MessageLog[];
}

export interface Keyword {
  id: number;
  rule_id: number;
  keyword: string;
  is_blacklist: boolean;
  created_at: string;
}

export interface ReplaceRule {
  id: number;
  rule_id: number;
  name?: string;
  pattern: string;
  replacement: string;
  priority: number;
  is_regex: boolean;
  is_active: boolean;
  created_at: string;
}

// 表单数据类型
export interface CreateRuleDto {
  name: string;
  source_chat_id: string;
  source_chat_name?: string;
  target_chat_id: string;
  target_chat_name?: string;
  
  // 功能开关
  is_active?: boolean;
  enable_keyword_filter?: boolean;
  enable_regex_replace?: boolean;
  
  // 客户端选择
  client_id?: string;
  client_type?: 'user' | 'bot';
  
  // 消息类型支持
  enable_text?: boolean;
  enable_media?: boolean;
  enable_photo?: boolean;
  enable_video?: boolean;
  enable_document?: boolean;
  enable_audio?: boolean;
  enable_voice?: boolean;
  enable_sticker?: boolean;
  enable_animation?: boolean;
  enable_webpage?: boolean;
  
  // 高级设置
  forward_delay?: number;
  max_message_length?: number;
  enable_link_preview?: boolean;
  
  // 时间过滤设置
  time_filter_type?: 'always' | 'after_start' | 'time_range' | 'from_time' | 'today_only' | 'business_hours' | 'non_business_hours';
  start_time?: string;
  end_time?: string;
}

export interface UpdateRuleDto extends Partial<CreateRuleDto> {
}

export interface CreateKeywordDto {
  rule_id: number;
  keyword: string;
  is_blacklist?: boolean;
}

export interface CreateReplaceRuleDto {
  rule_id: number;
  name?: string;
  pattern: string;
  replacement: string;
  priority?: number;
  is_regex?: boolean;
  is_active?: boolean;
}

// 规则筛选器
export interface RuleFilters {
  search?: string;
  is_active?: boolean;
  source_chat?: string;
  target_chat?: string;
  page?: number;
  pageSize?: number;
}

// 消息日志类型
export interface MessageLog {
  id: number;
  rule_id: number;
  rule_name?: string;
  source_chat_id: string;
  source_chat_name?: string;
  target_chat_id: string;
  target_chat_name?: string;
  message_id: number;
  forwarded_message_id?: number;
  message_type: string;
  message_text?: string;
  status: 'success' | 'failed' | 'filtered';
  error_message?: string;
  created_at: string;
}

export interface LogFilters {
  rule_id?: number;
  status?: 'success' | 'failed' | 'filtered' | 'all';
  message_type?: string;
  start_date?: string;
  end_date?: string;
  date?: string;
  search?: string;
  page?: number;
  limit?: number;
  pageSize?: number;
}

// 客户端相关类型
export interface TelegramClient {
  client_id: string;
  client_type: 'user' | 'bot';
  running: boolean;
  connected: boolean;
  user_info?: {
    id?: number;
    username?: string;
    first_name?: string;
    last_name?: string;
    phone?: string;
    bot?: boolean;
  };
  monitored_chats: string[];
  thread_alive: boolean;
}

export interface ClientsResponse {
  success: boolean;
  clients: Record<string, TelegramClient>;
  message?: string;
}
