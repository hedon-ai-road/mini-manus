'use client'

import { Globe } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface BrowserToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function BrowserTool({ label, onClick, hasError }: BrowserToolProps) {
  return <ToolBadge icon={Globe} label={label} onClick={onClick} hasError={hasError} />
}
