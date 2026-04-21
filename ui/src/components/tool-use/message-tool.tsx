'use client'

export interface MessageToolProps {
  label: string
  onClick?: () => void
  hasError?: boolean
}

export function MessageTool({ label }: MessageToolProps) {
  return <p className="text-gray-700 text-sm min-w-0">{label}</p>
}
