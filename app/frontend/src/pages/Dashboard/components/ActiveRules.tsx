import React from 'react';
import { Card, List, Tag, Space, Typography, Button, Switch, message } from 'antd';
import { SettingOutlined, EyeOutlined, MessageOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { rulesApi } from '../../../services/rules.ts';
import type { ForwardRule } from '../../../types/rule.ts';

const { Text } = Typography;

interface ActiveRulesProps {
  rules: ForwardRule[];
  loading?: boolean;
}

const ActiveRules: React.FC<ActiveRulesProps> = ({ rules, loading = false }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // 切换规则状态 - 优化版（简单乐观更新）
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      rulesApi.toggle(id, enabled),
    onMutate: async ({ id, enabled }) => {
      // 取消正在进行的查询，防止覆盖乐观更新
      await queryClient.cancelQueries({ queryKey: ['rules'] });
      
      // 获取当前数据快照
      const previousRules = queryClient.getQueryData<ForwardRule[]>(['rules']);
      
      // 乐观更新：立即修改UI状态
      if (previousRules) {
        const updatedRules = previousRules.map(rule => 
          rule.id === id ? { ...rule, is_active: enabled, updated_at: new Date().toISOString() } : rule
        );
        queryClient.setQueryData(['rules'], updatedRules);
      }
      
      return { previousRules };
    },
    onSuccess: (response, variables) => {
      console.log('🔄 规则状态切换成功:', variables);
      message.success(`规则${variables.enabled ? '已启用' : '已禁用'}`);
      
      // 用API返回的实际数据更新缓存，确保数据一致性
      if (response && response.rule) {
        const currentRules = queryClient.getQueryData<ForwardRule[]>(['rules']);
        if (currentRules) {
          const updatedRules = currentRules.map(rule => 
            rule.id === response.rule.id ? response.rule : rule
          );
          queryClient.setQueryData(['rules'], updatedRules);
        }
      }
      
      // 更新统计数据
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (error, variables, context) => {
      console.error('❌ 规则状态切换失败:', error, variables);
      message.error('规则状态更新失败');
      // 失败时回滚乐观更新
      if (context?.previousRules) {
        queryClient.setQueryData(['rules'], context.previousRules);
      }
    },
  });

  const handleRuleToggle = (ruleId: number, checked: boolean) => {
    toggleMutation.mutate({ id: ruleId, enabled: checked });
  };

  const getFeatureTags = (rule: ForwardRule) => {
    const features = [];
    
    if (rule.enable_keyword_filter) {
      features.push(<Tag key="keyword" color="blue">关键词过滤</Tag>);
    }
    
    if (rule.enable_regex_replace) {
      features.push(<Tag key="regex" color="green">正则替换</Tag>);
    }
    
    return features;
  };

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          活跃规则
        </Space>
      }
      className="glass-card"
      extra={
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => navigate('/rules')}
        >
          管理规则
        </Button>
      }
    >
      <List
        loading={loading}
        dataSource={rules.slice(0, 6)} // 只显示前6个
        locale={{
          emptyText: '暂无活跃规则',
        }}
        renderItem={(rule) => (
          <List.Item
            style={{
              padding: '12px 0',
              borderBottom: '1px solid var(--border-color)',
            }}
          >
            <div style={{ width: '100%' }}>
              {/* 规则名称和状态 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text strong ellipsis style={{ maxWidth: '70%' }}>
                  {rule.name}
                </Text>
                <Switch
                  size="small"
                  checked={rule.is_active}
                  onChange={(checked) => handleRuleToggle(rule.id, checked)}
                  loading={toggleMutation.isPending}
                />
              </div>

              {/* 转发路径 */}
              <div style={{ marginBottom: 8 }}>
                <Space size={4} style={{ fontSize: 12 }}>
                  <Text type="secondary" ellipsis style={{ maxWidth: 80 }}>
                    {rule.source_chat_name || rule.source_chat_id}
                  </Text>
                  <MessageOutlined style={{ color: 'var(--text-tertiary)' }} />
                  <Text type="secondary" ellipsis style={{ maxWidth: 80 }}>
                    {rule.target_chat_name || rule.target_chat_id}
                  </Text>
                </Space>
              </div>

              {/* 功能标签 */}
              <div>
                <Space size={4} wrap>
                  {getFeatureTags(rule)}
                </Space>
              </div>
            </div>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default ActiveRules;
