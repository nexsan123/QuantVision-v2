/**
 * 7步向导导航组件
 */
import { Steps } from 'antd'
import { CheckCircleOutlined, LoadingOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { StepMeta, StepStatus } from '@/types/strategy'

interface WizardStepsProps {
  steps: StepMeta[]
  currentStep: number
  onStepClick?: (stepIndex: number) => void
}

const statusIcons: Record<StepStatus, React.ReactNode> = {
  completed: <CheckCircleOutlined className="text-green-500" />,
  current: <LoadingOutlined className="text-primary-500" />,
  pending: <ClockCircleOutlined className="text-gray-500" />,
  error: <span className="text-red-500">!</span>,
}

export default function WizardSteps({ steps, currentStep, onStepClick }: WizardStepsProps) {
  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-4 mb-6">
      <Steps
        current={currentStep}
        size="small"
        onChange={onStepClick}
        items={steps.map((step, index) => ({
          title: (
            <span className={index === currentStep ? 'text-primary-500 font-medium' : ''}>
              {step.title}
            </span>
          ),
          description: (
            <span className="text-xs text-gray-500">{step.description}</span>
          ),
          icon: statusIcons[step.status],
          status: step.status === 'completed' ? 'finish' :
                  step.status === 'current' ? 'process' :
                  step.status === 'error' ? 'error' : 'wait',
        }))}
      />
    </div>
  )
}
