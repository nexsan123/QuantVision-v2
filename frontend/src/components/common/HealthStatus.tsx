/**
 * 系统健康状态组件
 * Sprint 12: T31 - 健康检查端点
 *
 * 显示系统各组件健康状态
 */

import React from 'react'
import { Card, Tag, Tooltip, Progress, Space, Typography, Descriptions, Spin } from 'antd'
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  QuestionCircleOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  ApiOutlined,
  HddOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useDetailedHealth, useConnectionCheck } from '../../hooks/useHealth'

const { Text } = Typography

// ==================== 状态图标 ====================

interface StatusIconProps {
  status: string
}

function StatusIcon({ status }: StatusIconProps) {
  switch (status) {
    case 'healthy':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />
    case 'degraded':
      return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
    case 'unhealthy':
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
    case 'unconfigured':
      return <QuestionCircleOutlined style={{ color: '#8c8c8c' }} />
    default:
      return <QuestionCircleOutlined style={{ color: '#8c8c8c' }} />
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'success'
    case 'degraded':
      return 'warning'
    case 'unhealthy':
      return 'error'
    default:
      return 'default'
  }
}

// ==================== 组件健康卡片 ====================

interface ComponentCardProps {
  name: string
  icon: React.ReactNode
  status: string
  latency?: number
  details?: Record<string, unknown>
}

function ComponentCard({ name, icon, status, latency, details }: ComponentCardProps) {
  return (
    <Card
      size="small"
      style={{
        background: 'rgba(255,255,255,0.02)',
        borderColor: status === 'healthy' ? 'rgba(82,196,26,0.3)' :
                     status === 'unhealthy' ? 'rgba(255,77,79,0.3)' :
                     'rgba(255,255,255,0.1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Space>
          {icon}
          <Text strong>{name}</Text>
        </Space>
        <Space>
          {latency !== undefined && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {latency.toFixed(0)}ms
            </Text>
          )}
          <Tag color={getStatusColor(status)} icon={<StatusIcon status={status} />}>
            {status}
          </Tag>
        </Space>
      </div>
      {details && Object.keys(details).length > 0 && (
        <div style={{ marginTop: 8, fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
          {Object.entries(details)
            .filter(([key]) => !['status', 'latency_ms'].includes(key))
            .slice(0, 2)
            .map(([key, value]) => (
              <div key={key}>
                {key}: {String(value)}
              </div>
            ))}
        </div>
      )}
    </Card>
  )
}

// ==================== 系统资源指标 ====================

interface SystemMetricsProps {
  cpu: number
  memory: { percent: number; used_gb: number; total_gb: number }
  disk: { percent: number; used_gb: number; total_gb: number }
}

function SystemMetrics({ cpu, memory, disk }: SystemMetricsProps) {
  const getProgressColor = (percent: number) => {
    if (percent >= 90) return '#ff4d4f'
    if (percent >= 70) return '#faad14'
    return '#52c41a'
  }

  return (
    <Card
      size="small"
      title={<><HddOutlined /> 系统资源</>}
      style={{ background: 'rgba(255,255,255,0.02)' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <Text type="secondary">CPU</Text>
            <Text>{cpu.toFixed(1)}%</Text>
          </div>
          <Progress
            percent={cpu}
            showInfo={false}
            strokeColor={getProgressColor(cpu)}
            trailColor="rgba(255,255,255,0.1)"
            size="small"
          />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <Text type="secondary">内存</Text>
            <Text>{memory.used_gb.toFixed(1)} / {memory.total_gb.toFixed(1)} GB</Text>
          </div>
          <Progress
            percent={memory.percent}
            showInfo={false}
            strokeColor={getProgressColor(memory.percent)}
            trailColor="rgba(255,255,255,0.1)"
            size="small"
          />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <Text type="secondary">磁盘</Text>
            <Text>{disk.used_gb.toFixed(1)} / {disk.total_gb.toFixed(1)} GB</Text>
          </div>
          <Progress
            percent={disk.percent}
            showInfo={false}
            strokeColor={getProgressColor(disk.percent)}
            trailColor="rgba(255,255,255,0.1)"
            size="small"
          />
        </div>
      </Space>
    </Card>
  )
}

// ==================== 完整健康状态面板 ====================

interface HealthStatusPanelProps {
  pollInterval?: number
}

export function HealthStatusPanel({ pollInterval = 30000 }: HealthStatusPanelProps) {
  const { health, loading, error, refetch, isHealthy, isDegraded } = useDetailedHealth({
    pollInterval,
    enabled: true,
  })

  if (loading && !health) {
    return (
      <Card style={{ textAlign: 'center', padding: 24 }}>
        <Spin tip="加载健康状态..." />
      </Card>
    )
  }

  if (error) {
    return (
      <Card
        title="系统健康"
        extra={<ReloadOutlined onClick={refetch} style={{ cursor: 'pointer' }} />}
        style={{ borderColor: 'rgba(255,77,79,0.3)' }}
      >
        <Text type="danger">无法获取健康状态: {error.message}</Text>
      </Card>
    )
  }

  if (!health) return null

  const { components, version, environment, uptime_human, python_version } = health

  return (
    <Card
      title={
        <Space>
          <CloudServerOutlined />
          系统健康
          <Tag color={getStatusColor(health.status)}>{health.status.toUpperCase()}</Tag>
        </Space>
      }
      extra={
        <Tooltip title="刷新">
          <ReloadOutlined onClick={refetch} style={{ cursor: 'pointer' }} />
        </Tooltip>
      }
      style={{
        borderColor: isHealthy ? 'rgba(82,196,26,0.3)' :
                     isDegraded ? 'rgba(250,173,20,0.3)' :
                     'rgba(255,77,79,0.3)',
      }}
    >
      {/* 基本信息 */}
      <Descriptions size="small" column={4} style={{ marginBottom: 16 }}>
        <Descriptions.Item label="版本">{version}</Descriptions.Item>
        <Descriptions.Item label="环境">{environment}</Descriptions.Item>
        <Descriptions.Item label="运行时间">{uptime_human}</Descriptions.Item>
        <Descriptions.Item label="Python">{python_version}</Descriptions.Item>
      </Descriptions>

      {/* 组件状态 */}
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 12,
        }}>
          <ComponentCard
            name="数据库"
            icon={<DatabaseOutlined />}
            status={components.database?.status || 'unknown'}
            latency={components.database?.latency_ms}
          />
          <ComponentCard
            name="Redis"
            icon={<DatabaseOutlined />}
            status={components.redis?.status || 'unknown'}
            latency={components.redis?.latency_ms}
            details={{ memory_mb: components.redis?.used_memory_mb }}
          />
          <ComponentCard
            name="Alpaca"
            icon={<ApiOutlined />}
            status={components.alpaca?.status || 'unknown'}
            details={components.alpaca}
          />
          <ComponentCard
            name="S3 存储"
            icon={<HddOutlined />}
            status={components.s3_storage?.status || 'unknown'}
          />
        </div>

        {/* 系统资源 */}
        {components.system && !('error' in components.system) && (
          <SystemMetrics
            cpu={components.system.cpu_percent}
            memory={components.system.memory}
            disk={components.system.disk}
          />
        )}
      </Space>
    </Card>
  )
}

// ==================== 简洁状态指示器 ====================

export function HealthIndicator() {
  const { isConnected, checking, check } = useConnectionCheck()

  return (
    <Tooltip title={isConnected ? '系统正常' : '连接断开'}>
      <Tag
        color={checking ? 'processing' : isConnected ? 'success' : 'error'}
        icon={checking ? <Spin size="small" /> : <StatusIcon status={isConnected ? 'healthy' : 'unhealthy'} />}
        onClick={check}
        style={{ cursor: 'pointer' }}
      >
        {checking ? '检查中...' : isConnected ? '在线' : '离线'}
      </Tag>
    </Tooltip>
  )
}

export default HealthStatusPanel
