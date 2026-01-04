/**
 * 向导/工作流模式切换组件
 */
import { Segmented } from 'antd'
import { AppstoreOutlined, NodeIndexOutlined } from '@ant-design/icons'
import { BuilderMode } from '@/types/strategy'

interface ModeToggleProps {
  mode: BuilderMode
  onChange: (mode: BuilderMode) => void
}

export default function ModeToggle({ mode, onChange }: ModeToggleProps) {
  return (
    <Segmented
      value={mode}
      onChange={(value) => onChange(value as BuilderMode)}
      options={[
        {
          label: (
            <div className="flex items-center gap-2 px-2">
              <AppstoreOutlined />
              <span>向导模式</span>
            </div>
          ),
          value: 'wizard',
        },
        {
          label: (
            <div className="flex items-center gap-2 px-2">
              <NodeIndexOutlined />
              <span>工作流模式</span>
            </div>
          ),
          value: 'workflow',
        },
      ]}
    />
  )
}
