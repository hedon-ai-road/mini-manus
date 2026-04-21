'use client'

import { FileSearch } from 'lucide-react'
import { ToolBadge } from './tool-badge'

export interface FileToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function FileTool({ label, onClick, hasError }: FileToolProps) {
  return <ToolBadge icon={FileSearch} label={label} onClick={onClick} hasError={hasError} />
}
