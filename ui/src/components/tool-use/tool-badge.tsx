'use client'

import type { LucideIcon } from 'lucide-react'
import { AlertCircle } from 'lucide-react'

export interface ToolBadgeProps {
  icon: LucideIcon
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function ToolBadge({ icon: Icon, label, onClick, hasError }: ToolBadgeProps) {
  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } } : undefined}
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 border text-sm w-fit max-w-full min-w-0 cursor-pointer transition-colors ${
        hasError
          ? 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100/60'
          : 'border-gray-200 bg-gray-100 text-gray-700 hover:bg-gray-200/60'
      }`}
    >
      <span className={`shrink-0 flex items-center justify-center ${hasError ? 'text-red-500' : 'text-gray-600'}`}>
        {hasError ? <AlertCircle size={16} className="shrink-0" /> : <Icon size={16} className="shrink-0" />}
      </span>
          <span className="truncate max-w-120">{label}</span>
    </div>
  )
}
