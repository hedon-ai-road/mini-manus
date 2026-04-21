'use client'

import { Wrench } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface McpToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function McpTool({ label, onClick, hasError }: McpToolProps) {
  return <ToolBadge icon={Wrench} label={label} onClick={onClick} hasError={hasError} />
}
