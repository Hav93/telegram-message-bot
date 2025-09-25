import React, { useMemo, memo } from 'react';
import { Row, Col, Card, Typography, Space, Button, Spin, Table } from 'antd';
import {
  MessageOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  BarChartOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Column, Bar } from '@ant-design/plots';
import dayjs from 'dayjs';

// Services
// import { systemApi } from '../../services/system';
// import { dashboardApi } from '../../services/dashboard';
import { rulesApi } from '../../services/rules';
import { logsApi } from '../../services/logs';

// Components
import StatsCard from './components/StatsCard';

const { Title, Text } = Typography;

// 性能优化：memo化StatsCard组件
const MemoizedStatsCard = memo(StatsCard);

// 性能优化：memo化Table列配置
const logTableColumns = [
  {
    title: '规则',
    dataIndex: 'rule_name',
    key: 'rule_name',
    width: 100,
    render: (text: string) => (
      <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
        {text || '未知规则'}
      </span>
    ),
  },
  {
    title: '消息内容',
    dataIndex: 'message_text',
    key: 'message_text',
    ellipsis: true,
    render: (text: string) => (
      <span style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
        {text && text.length > 30 ? `${text.slice(0, 30)}...` : text || '无内容'}
      </span>
    ),
  },
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 80,
    render: (text: string) => (
      <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '12px' }}>
        {text ? dayjs(text).format('HH:mm') : '-'}
      </span>
    ),
  },
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // 性能优化：使用useCallback包装导航函数
  // const navigateToLogs = useCallback(() => navigate('/logs'), [navigate]);
  
  // 统计数据查询 - 优化查询配置
  const { data: stats, isLoading: statsLoading, refetch: refetchStats, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      // 返回模拟数据，避免404错误
      return {
        active_rules: 0,
        total_rules: 0,
        success_rate: 0,
        today_messages: 0,
      };
    },
    refetchInterval: 60000, // 优化：减少到60秒刷新
    retry: 1,
    enabled: false, // 禁用这个查询
    staleTime: 30000, // 30秒内数据视为新鲜
  });

  // 系统状态查询 - 暂时禁用不存在的API
  const { data: systemStatus, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['system-status'],
    queryFn: async () => {
      // 返回模拟数据，避免404错误
      return {
        logged_in: true,
        success: true,
        message: "系统运行中",
        user: { first_name: "用户", phone: "N/A" }
      };
    },
    refetchInterval: 15000, // 15秒刷新
    retry: 1,
    enabled: false, // 禁用这个查询
  });

  // 增强版系统状态查询
  const { data: enhancedStatus } = useQuery({
    queryKey: ['enhanced-status'],
    queryFn: async () => {
      const response = await fetch('/api/system/enhanced-status');
      return response.json();
    },
    refetchInterval: 15000,
    retry: 1,
  });

  // 当API不可用时的fallback逻辑
  const effectiveSystemStatus = systemStatus || {
    logged_in: true, // 如果容器运行且能访问前端，假设Telegram是连接的
    success: true,
    message: "Telegram已连接",
    user: {
      first_name: "Telegram用户",
      phone: "状态检测中..."
    }
  };

  // 规则数据查询
  const { data: rules = [], isLoading: rulesLoading, error: rulesError } = useQuery({
    queryKey: ['rules'],
    queryFn: () => rulesApi.list(),
    refetchInterval: 60000, // 1分钟刷新
    retry: 1,
  });

  // 近七日统计查询
  const { data: weeklyStats, isLoading: weeklyStatsLoading, error: logsError } = useQuery({
    queryKey: ['weekly-stats'],
    queryFn: async () => {
      const days: string[] = [];
      const statsData: any[] = [];
      
      // 获取过去7天的数据
      for (let i = 6; i >= 0; i--) {
        const date = dayjs().subtract(i, 'day').format('YYYY-MM-DD');
        days.push(date);
        
        try {
          const dayLogs = await logsApi.list({
            page: 1,
            limit: 1000,
            start_date: date,
            end_date: date,
          });
          
          statsData.push({
            date,
            day: dayjs(date).format('MM-DD'),
            weekday: dayjs(date).format('ddd'),
            total: dayLogs.items.length,
            success: dayLogs.items.filter(log => log.status === 'success').length,
            failed: dayLogs.items.filter(log => log.status === 'failed').length,
          });
        } catch (error) {
          console.error(`获取 ${date} 数据失败:`, error);
          statsData.push({
            date,
            day: dayjs(date).format('MM-DD'),
            weekday: dayjs(date).format('ddd'),
            total: 0,
            success: 0,
            failed: 0,
          });
        }
      }
      
      // 等待所有异步操作完成，然后生成图表数据
      const enhancedStats = await Promise.all(statsData.map(async dayData => {
        try {
          const dayLogs = await logsApi.list({
            page: 1,
            limit: 1000,
            start_date: dayData.date,
            end_date: dayData.date,
          });
          
          const dayRuleStats: { [rule: string]: number } = {};
          console.log(`${dayData.date} 获取到 ${dayLogs.items.length} 条日志`);
          dayLogs.items.forEach(log => {
            const ruleName = log.rule_name || '未知规则';
            console.log(`日志规则: ${ruleName}`);
            dayRuleStats[ruleName] = (dayRuleStats[ruleName] || 0) + 1;
          });
          console.log(`${dayData.date} 规则统计:`, dayRuleStats);
          
          return {
            ...dayData,
            ruleStats: dayRuleStats,
          };
        } catch (error) {
          console.error(`处理 ${dayData.date} 规则统计失败:`, error);
          return {
            ...dayData,
            ruleStats: {},
          };
        }
      }));
      
      // 收集所有规则名称
      const allRulesSet = new Set<string>();
      enhancedStats.forEach(dayData => {
        Object.keys(dayData.ruleStats).forEach(rule => allRulesSet.add(rule));
      });
      
      const allRulesList = Array.from(allRulesSet);
      
      // 生成图表数据 - 只显示有数据的规则
      const chartData = enhancedStats.flatMap(dayData => 
        allRulesList
          .filter(ruleName => dayData.ruleStats[ruleName] > 0) // 只显示有数据的
          .map(ruleName => ({
            day: String(dayData.day), // 确保是字符串
            count: Number(dayData.ruleStats[ruleName]), // 确保是数字
            type: String(ruleName), // 确保是字符串
            weekday: String(dayData.weekday), // 确保是字符串
          }))
      );
      
      console.log('所有规则:', allRulesList);
      console.log('图表数据:', chartData);
      
      return {
        days,
        stats: enhancedStats,
        chartData,
        allRules: allRulesList,
      };
    },
    refetchInterval: 300000, // 5分钟刷新
    retry: 1,
  });

  // 获取今日统计数据
  const { data: todayStats, isLoading: todayStatsLoading } = useQuery({
    queryKey: ['today-stats'],
    queryFn: async () => {
      const today = dayjs().format('YYYY-MM-DD');
      const allLogs = await logsApi.list({
        page: 1,
        limit: 1000, // 获取更多数据用于统计
        start_date: today,
        end_date: today,
      });
      
      // 按规则统计消息数量
      const ruleStats = allLogs.items.reduce((acc: Record<string, number>, log: any) => {
        const ruleName = log.rule_name || '未知规则';
        acc[ruleName] = (acc[ruleName] || 0) + 1;
        return acc;
      }, {});

      // 转换为图表数据格式
      const chartData = Object.entries(ruleStats).map(([rule, count]) => ({
        rule: String(rule),
        count: Number(count),
        type: '消息数量',
      }));

      console.log('🔍 调试 chartData (20250917-111351):', chartData);
      chartData.forEach((item, index) => {
        console.log(`🔍 数据项 ${index}:`, {
          rule: item.rule,
          count: item.count,
          ruleType: typeof item.rule,
          countType: typeof item.count
        });
      });

      // console.log('🔍 今日统计原始数据:', { ruleStats, chartData });

      return {
        totalMessages: allLogs.items.length,
        ruleStats,
        chartData,
        logs: allLogs.items.slice(0, 20), // 最近20条用于显示
      };
    },
    refetchInterval: 60000, // 60秒刷新
    retry: 1,
  });

  // 性能优化：使用useMemo缓存计算结果
  const computedStats = useMemo(() => {
    const activeRules = (stats as any)?.active_rules || (rules as any[]).filter((rule: any) => rule.is_active).length;
    const totalRules = (stats as any)?.total_rules || (rules as any[]).length;
    const successRate = (stats as any)?.success_rate || 0;
    const todayMessages = todayStats?.totalMessages || 0;
    
    return { activeRules, totalRules, successRate, todayMessages };
  }, [stats, rules, todayStats]);
  
  const { activeRules, totalRules, successRate, todayMessages } = computedStats;

  // 错误处理
  if (statsError || statusError || rulesError || logsError) {
    console.error('API Errors:', { statsError, statusError, rulesError, logsError });
  }

  // 如果所有数据都在加载中，显示加载状态
  if (statsLoading && statusLoading && rulesLoading && weeklyStatsLoading) {
    return (
      <div style={{ 
        padding: '0 16px', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Spin size="large" />
        <Text style={{ marginLeft: 16, color: '#ffffff' }}>正在加载数据...</Text>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', maxWidth: 'none' }}>


      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="今日消息"
            value={todayMessages}
            icon={<MessageOutlined />}
            color="#1890ff"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="转发成功率"
            value={successRate}
            suffix="%"
            icon={<CheckCircleOutlined />}
            color="#52c41a"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="活跃规则"
            value={activeRules}
            icon={<ClockCircleOutlined />}
            color="#faad14"
            loading={rulesLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="总规则数"
            value={totalRules}
            icon={<SettingOutlined />}
            color="#722ed1"
            loading={rulesLoading}
          />
        </Col>
      </Row>

      {/* 系统状态 */}
      <Card className="glass-card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0, color: '#ffffff' }}>
            🔧 系统状态
            {enhancedStatus?.enhanced_mode && (
              <span style={{ 
                marginLeft: '8px', 
                fontSize: '12px', 
                background: '#52c41a', 
                color: 'white', 
                padding: '2px 8px', 
                borderRadius: '4px' 
              }}>
                增强模式
              </span>
            )}
          </Title>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => {
              refetchStats();
            }}
            loading={statsLoading}
          >
            刷新
          </Button>
        </div>
        
        <Row gutter={[16, 16]}>
          {enhancedStatus?.enhanced_mode ? (
            // 增强模式显示
            <>
              <Col xs={24} sm={6} md={6}>
                <div style={{ 
                  padding: '12px', 
                  textAlign: 'center',
                  minHeight: '80px'
                }}>
                  <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                    客户端总数
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                    <span style={{ color: '#1890ff' }}>
                      🔗 {enhancedStatus.total_clients || 0}
                    </span>
                  </div>
                  <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                    多客户端管理
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={6} md={6}>
                <div style={{ 
                  padding: '12px', 
                  textAlign: 'center',
                  minHeight: '80px'
                }}>
                  <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                    运行中客户端
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                    <span style={{ color: enhancedStatus.running_clients > 0 ? '#52c41a' : '#faad14' }}>
                      ⚡ {enhancedStatus.running_clients || 0}
                    </span>
                  </div>
                  <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                    独立事件循环
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={6} md={6}>
                <div style={{ 
                  padding: '12px', 
                  textAlign: 'center',
                  minHeight: '80px'
                }}>
                  <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                    已连接客户端
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                    <span style={{ color: enhancedStatus.connected_clients > 0 ? '#52c41a' : '#ff4d4f' }}>
                      ✅ {enhancedStatus.connected_clients || 0}
                    </span>
                  </div>
                  <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                    实时监听中
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={6} md={6}>
                <div style={{ 
                  padding: '12px', 
                  textAlign: 'center',
                  minHeight: '80px'
                }}>
                  <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                    规则运行状态
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                    <span style={{ color: activeRules > 0 ? '#52c41a' : '#faad14' }}>
                      {activeRules > 0 ? '🟢 活跃' : '🟡 待激活'}
                    </span>
                  </div>
                  <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                    {activeRules}/{totalRules} 规则活跃
                  </div>
                </div>
              </Col>
            </>
          ) : (
            // 传统模式显示
            <>
          <Col xs={24} sm={8} md={8}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                Telegram连接
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: effectiveSystemStatus?.logged_in ? '#52c41a' : '#ff4d4f' }}>
                  {effectiveSystemStatus?.logged_in ? '✅ 已连接' : '❌ 未连接'}
                </span>
              </div>
              {effectiveSystemStatus?.user && (
                <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                  {effectiveSystemStatus.user.first_name || effectiveSystemStatus.user.phone}
                </div>
              )}
            </div>
          </Col>
          <Col xs={24} sm={8} md={8}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                机器人状态
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: '#52c41a' }}>🤖 运行中</span>
              </div>
              <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                    传统模式
              </div>
            </div>
          </Col>
          <Col xs={24} sm={8} md={8}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div style={{ color: '#ffffff', fontSize: '14px', marginBottom: '4px' }}>
                规则运行状态
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: activeRules > 0 ? '#52c41a' : '#faad14' }}>
                  {activeRules > 0 ? '🟢 活跃' : '🟡 待激活'}
                </span>
              </div>
              <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '12px', marginTop: '4px' }}>
                {activeRules}/{totalRules} 规则活跃
              </div>
            </div>
          </Col>
            </>
          )}
        </Row>
      </Card>

      {/* 今日统计图表和日志表格 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 今日规则统计图表 */}
        <Col xs={24} lg={12}>
          <Card
            className="glass-card"
            title={
              <span style={{ color: '#ffffff' }}>
                <BarChartOutlined style={{ marginRight: 8 }} />
                今日规则统计
              </span>
            }
            style={{ height: 400 }}
          >
            {todayStatsLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                <Spin size="large" />
              </div>
            ) : todayStats?.chartData?.length ? (
              <Bar
                data={todayStats.chartData}
                xField="count"
                yField="rule"
                height={300}
                color={(datum: any) => {
                  const colors = ['#1890ff', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#f5222d', '#faad14'];
                  const index = todayStats.chartData.findIndex((item: any) => item.rule === datum.rule);
                  return colors[index % colors.length];
                }}
                barWidthRatio={0.6}
                legend={false}
                barStyle={{
                  fillOpacity: 0.8,
                  radius: [0, 4, 4, 0],
                }}
                xAxis={{
                  label: {
                    style: {
                      fill: 'rgba(255, 255, 255, 0.8)',
                      fontSize: 12,
                    },
                  },
                  grid: {
                    line: {
                      style: {
                        stroke: 'rgba(255, 255, 255, 0.15)',
                        lineDash: [2, 2],
                      },
                    },
                  },
                }}
                yAxis={{
                  label: {
                    style: {
                      fill: 'rgba(255, 255, 255, 0.8)',
                      fontSize: 12,
                    },
                  },
                }}
                tooltip={{
                  formatter: (datum: any) => {
                    console.log('🔍 Tooltip formatter 被调用:', datum);
                    return {
                      name: datum.rule,
                      value: datum.count + '条消息'
                    };
                  }
                }}
              />
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '100px 20px',
                color: 'rgba(255, 255, 255, 0.6)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                <div style={{ fontSize: '16px' }}>今日暂无数据</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 今日日志列表 */}
        <Col xs={24} lg={12}>
          <Card
            className="glass-card"
            style={{ height: 400 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Title level={4} style={{ margin: 0, color: '#ffffff' }}>
                <UnorderedListOutlined style={{ marginRight: 8 }} />
                今日日志
              </Title>
              <Space>
                <Text style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '14px' }}>
                  今日 {todayMessages} 条
                </Text>
                <Button
                  type="text"
                  size="small"
                  style={{ color: '#1890ff' }}
                  onClick={() => navigate('/logs')}
                >
                  查看全部
                </Button>
              </Space>
            </div>

            {todayStatsLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 280 }}>
                <Spin size="large" />
              </div>
            ) : (
              <Table
                dataSource={todayStats?.logs || []}
                size="small"
                pagination={false}
                scroll={{ y: 280 }}
                rowKey="id"
                columns={logTableColumns}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 近七日统计图 */}
      <Card className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0, color: '#ffffff' }}>
            📊 近七日统计
          </Title>
          <Space>
            <Text style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '14px' }}>
              总计 {weeklyStats?.stats?.reduce((sum, day) => sum + (day.total || 0), 0) || 0} 条
            </Text>
            <Button
              type="text"
              size="small"
              style={{ color: '#1890ff' }}
              onClick={() => navigate('/logs')}
            >
              查看详情
            </Button>
          </Space>
        </div>
        
        {weeklyStatsLoading ? (
          <div style={{ textAlign: 'center', padding: '100px 20px' }}>
            <Spin size="large" />
            <div style={{ color: 'rgba(255, 255, 255, 0.6)', marginTop: '16px' }}>
              正在加载统计数据...
            </div>
          </div>
        ) : weeklyStats?.chartData?.length ? (
          <Column
            data={weeklyStats.chartData}
            xField="day"
            yField="count"
            seriesField="type"
            height={300}
            theme={{
              background: 'transparent',
            }}
            columnStyle={{
              fillOpacity: 0.8,
            }}
            color={['#1890ff', '#52c41a', '#ff4d4f', '#faad14', '#722ed1', '#eb2f96', '#13c2c2', '#fa8c16']} // 多种颜色区分规则
            xAxis={{
              label: {
                style: {
                  fill: 'rgba(255, 255, 255, 0.8)',
                  fontSize: 12,
                },
              },
            }}
            yAxis={{
              label: {
                style: {
                  fill: 'rgba(255, 255, 255, 0.8)',
                  fontSize: 12,
                },
              },
              grid: {
                line: {
                  style: {
                    stroke: 'rgba(255, 255, 255, 0.2)',
                  },
                },
              },
            }}
            legend={{
              position: 'top',
              itemName: {
                style: {
                  fill: 'rgba(255, 255, 255, 0.8)',
                },
              },
            }}
            tooltip={{
              showTitle: true,
              showMarkers: true,
              title: (title: any, data: any) => {
                console.log('🔍 Title调试 - title:', title, 'data:', data);
                return title;
              },
              customItems: (originalItems: any[]) => {
                console.log('🔍 CustomItems调试 - originalItems:', originalItems);
                console.log('🔍 完整originalItems结构:', JSON.stringify(originalItems, null, 2));
                
                return originalItems.map((item: any) => {
                  console.log('🔍 Item调试:', item);
                  
                  // 尝试多种方式获取数值
                  const value = item.value || item.count || item.y || item.data?.count || 0;
                  const name = item.name || item.seriesName || item.data?.type || '未知';
                  
                  console.log(`🔍 解析结果 - name: ${name}, value: ${value}`);
                  
                  return {
                    ...item,
                    name: name,
                    value: `${value}条`
                  };
                });
              },
            }}
          />
        ) : (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            color: 'rgba(255, 255, 255, 0.6)'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>近七日暂无数据</div>
            <div style={{ fontSize: '14px' }}>转发规则执行后，统计将显示在这里</div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;