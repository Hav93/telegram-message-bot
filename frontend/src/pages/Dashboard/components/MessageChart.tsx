import React from 'react';
import { Skeleton } from 'antd';
// import ReactECharts from 'echarts-for-react';

interface MessageChartProps {
  data: Array<{
    date: string;
    count: number;
  }>;
  loading?: boolean;
}

const MessageChart: React.FC<MessageChartProps> = ({ data, loading = false }) => {
  if (loading) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  // 暂时显示占位内容，等ECharts版本问题解决后再启用
  return (
    <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <h3>消息统计图表</h3>
        <p>过去7天共 {data.reduce((sum, item) => sum + item.count, 0)} 条消息</p>
        <p style={{ color: '#999', fontSize: '12px' }}>图表功能正在完善中...</p>
      </div>
    </div>
  );
};

export default MessageChart;