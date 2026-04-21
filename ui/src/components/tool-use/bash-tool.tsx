'use client'

import { Terminal } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface BashToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function BashTool({ label, onClick, hasError }: BashToolProps) {
  return <ToolBadge icon={Terminal} label={label} onClick={onClick} hasError={hasError} />
}
