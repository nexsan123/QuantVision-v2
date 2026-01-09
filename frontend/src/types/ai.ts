/**
 * AI 连接状态类型定义
 * PRD 4.2
 */

// AI 状态类型
export type AIStatusType = 'connected' | 'connecting' | 'disconnected' | 'error';

// AI 连接状态
export interface AIConnectionStatus {
  isConnected: boolean;
  status: AIStatusType;
  modelName: string;
  lastHeartbeat?: string;
  latencyMs?: number;
  errorMessage?: string;
  canReconnect: boolean;
}

// AI 状态配置
export const AI_STATUS_CONFIG: Record<AIStatusType, {
  icon: string;
  text: string;
  color: string;
  bgColor: string;
}> = {
  connected: {
    icon: '🟢',
    text: 'AI已连接',
    color: '#22c55e',
    bgColor: 'bg-green-500/20',
  },
  connecting: {
    icon: '🟡',
    text: '正在连接...',
    color: '#eab308',
    bgColor: 'bg-yellow-500/20',
  },
  disconnected: {
    icon: '🔴',
    text: 'AI已断开',
    color: '#ef4444',
    bgColor: 'bg-red-500/20',
  },
  error: {
    icon: '🔴',
    text: '连接错误',
    color: '#ef4444',
    bgColor: 'bg-red-500/20',
  },
};

// 格式化延迟显示
export function formatLatency(ms?: number): string {
  if (ms === undefined || ms === null) return '';
  if (ms < 100) return `${ms}ms`;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}
