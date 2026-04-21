'use client'

import { SquareChevronRight } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface DefaultToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function DefaultTool({ label, onClick, hasError }: DefaultToolProps) {
  return <ToolBadge icon={SquareChevronRight} label={label} onClick={onClick} hasError={hasError} />
}
