'use client'

import { Search } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface SearchToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function SearchTool({ label, onClick, hasError }: SearchToolProps) {
  return <ToolBadge icon={Search} label={label} onClick={onClick} hasError={hasError} />
}
