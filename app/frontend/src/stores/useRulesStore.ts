import { create } from 'zustand';
import type { ForwardRule, RuleFilters } from '../types/rule';

// 规则管理状态
interface RulesState {
  // 规则列表
  rules: ForwardRule[];
  setRules: (rules: ForwardRule[]) => void;
  
  // 选中的规则
  selectedRule: ForwardRule | null;
  setSelectedRule: (rule: ForwardRule | null) => void;
  
  // 编辑模式
  editMode: boolean;
  setEditMode: (editMode: boolean) => void;
  
  // 筛选器
  filters: RuleFilters;
  setFilters: (filters: RuleFilters) => void;
  updateFilter: (key: keyof RuleFilters, value: any) => void;
  clearFilters: () => void;
  
  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;
  
  // 选中的规则IDs（用于批量操作）
  selectedRuleIds: number[];
  setSelectedRuleIds: (ids: number[]) => void;
  toggleSelectedRule: (id: number) => void;
  selectAllRules: (select: boolean) => void;
  
  // 规则操作
  addRule: (rule: ForwardRule) => void;
  updateRule: (rule: ForwardRule) => void;
  removeRule: (id: number) => void;
  removeRules: (ids: number[]) => void;
  
  // 搜索和排序
  searchText: string;
  setSearchText: (text: string) => void;
  sortBy: 'name' | 'created_at' | 'updated_at';
  sortOrder: 'asc' | 'desc';
  setSorting: (sortBy: RulesState['sortBy'], sortOrder: RulesState['sortOrder']) => void;
  
  // 过滤后的规则列表
  getFilteredRules: () => ForwardRule[];
  
  // 统计信息
  getStats: () => {
    total: number;
    active: number;
    inactive: number;
    withKeywords: number;
    withReplacements: number;
  };
}

export const useRulesStore = create<RulesState>((set, get) => ({
  // 初始状态
  rules: [],
  selectedRule: null,
  editMode: false,
  filters: {},
  loading: false,
  selectedRuleIds: [],
  searchText: '',
  sortBy: 'updated_at',
  sortOrder: 'desc',
  
  // 规则列表相关方法
  setRules: (rules) => set({ rules }),
  
  // 选中规则相关方法
  setSelectedRule: (rule) => set({ selectedRule: rule }),
  
  // 编辑模式相关方法
  setEditMode: (editMode) => set({ editMode }),
  
  // 筛选器相关方法
  setFilters: (filters) => set({ filters }),
  
  updateFilter: (key, value) => {
    const { filters } = get();
    set({
      filters: {
        ...filters,
        [key]: value,
      },
    });
  },
  
  clearFilters: () => set({ filters: {} }),
  
  // 加载状态相关方法
  setLoading: (loading) => set({ loading }),
  
  // 批量选择相关方法
  setSelectedRuleIds: (ids) => set({ selectedRuleIds: ids }),
  
  toggleSelectedRule: (id) => {
    const { selectedRuleIds } = get();
    const newIds = selectedRuleIds.includes(id)
      ? selectedRuleIds.filter(ruleId => ruleId !== id)
      : [...selectedRuleIds, id];
    set({ selectedRuleIds: newIds });
  },
  
  selectAllRules: (select) => {
    const { rules } = get();
    set({
      selectedRuleIds: select ? rules.map(rule => rule.id) : [],
    });
  },
  
  // 规则操作相关方法
  addRule: (rule) => {
    const { rules } = get();
    set({ rules: [rule, ...rules] });
  },
  
  updateRule: (updatedRule) => {
    const { rules } = get();
    set({
      rules: rules.map(rule => 
        rule.id === updatedRule.id ? updatedRule : rule
      ),
    });
  },
  
  removeRule: (id) => {
    const { rules, selectedRuleIds } = get();
    set({
      rules: rules.filter(rule => rule.id !== id),
      selectedRuleIds: selectedRuleIds.filter(ruleId => ruleId !== id),
    });
  },
  
  removeRules: (ids) => {
    const { rules, selectedRuleIds } = get();
    set({
      rules: rules.filter(rule => !ids.includes(rule.id)),
      selectedRuleIds: selectedRuleIds.filter(ruleId => !ids.includes(ruleId)),
    });
  },
  
  // 搜索和排序相关方法
  setSearchText: (text) => set({ searchText: text }),
  
  setSorting: (sortBy, sortOrder) => set({ sortBy, sortOrder }),
  
  // 获取过滤后的规则列表
  getFilteredRules: () => {
    const { rules, filters, searchText, sortBy, sortOrder } = get();
    
    let filtered = [...rules];
    
    // 文本搜索
    if (searchText) {
      const search = searchText.toLowerCase();
      filtered = filtered.filter(rule =>
        rule.name.toLowerCase().includes(search) ||
        rule.source_chat_name?.toLowerCase().includes(search) ||
        rule.target_chat_name?.toLowerCase().includes(search)
      );
    }
    
    // 状态筛选
    if (filters.is_active !== undefined) {
      filtered = filtered.filter(rule => rule.is_active === filters.is_active);
    }
    
    // 源聊天筛选
    if (filters.source_chat) {
      filtered = filtered.filter(rule => rule.source_chat_id === filters.source_chat);
    }
    
    // 目标聊天筛选
    if (filters.target_chat) {
      filtered = filtered.filter(rule => rule.target_chat_id === filters.target_chat);
    }
    
    // 排序
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy];
      let bValue: any = b[sortBy];
      
      // 处理时间类型
      if (sortBy.includes('_at')) {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }
      
      // 处理字符串类型
      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    return filtered;
  },
  
  // 获取统计信息
  getStats: () => {
    const { rules } = get();
    
    return {
      total: rules.length,
      active: rules.filter(rule => rule.is_active).length,
      inactive: rules.filter(rule => !rule.is_active).length,
      withKeywords: rules.filter(rule => rule.enable_keyword_filter).length,
      withReplacements: rules.filter(rule => rule.enable_regex_replace).length,
    };
  },
}));
