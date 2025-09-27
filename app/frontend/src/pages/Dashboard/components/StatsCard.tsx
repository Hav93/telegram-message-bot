import React from 'react';
import { Card, Statistic, Skeleton } from 'antd';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
  suffix?: string;
  prefix?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color,
  loading = false,
  suffix,
  prefix,
}) => {
  if (loading) {
    return (
      <Card className="glass-card-3d" style={{ height: 120 }}>
        <Skeleton active paragraph={{ rows: 1 }} />
      </Card>
    );
  }

  return (
    <Card
      className="glass-card-3d"
      style={{
        height: 120,
        position: 'relative',
        overflow: 'hidden',
      }}
      bodyStyle={{
        padding: 20,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      {/* 背景图标 */}
      <div
        style={{
          position: 'absolute',
          top: -10,
          right: -10,
          fontSize: 80,
          color: color,
          opacity: 0.15,
          transform: 'rotate(15deg)',
        }}
      >
        {icon}
      </div>

      {/* React标识 */}
      <div
        style={{
          position: 'absolute',
          top: 5,
          right: 5,
          fontSize: 12,
          color: color,
          opacity: 0.6,
          fontWeight: 'bold',
        }}
      >
        ⚛️
      </div>

      {/* 统计内容 */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div
          style={{
            color: 'rgba(255, 255, 255, 0.9)',
            fontSize: 14,
            marginBottom: 8,
            fontWeight: 500,
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)',
          }}
        >
          {title}
        </div>
        <Statistic
          value={value}
          suffix={suffix}
          prefix={prefix}
          valueStyle={{
            color: color,
            fontSize: 28,
            fontWeight: 'bold',
            textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
          }}
        />
      </div>

      {/* 左侧图标 */}
      <div
        style={{
          position: 'absolute',
          left: 16,
          top: 16,
          fontSize: 20,
          color: color,
        }}
      >
        {icon}
      </div>
    </Card>
  );
};

export default StatsCard;
