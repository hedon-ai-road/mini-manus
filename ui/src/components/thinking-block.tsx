'use client'

import { useState } from 'react'
import { ChevronDown, Brain } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ThinkingBlockProps {
  content: string
  status: 'thinking' | 'done'
  className?: string
}

export function ThinkingBlock({ content, status, className }: ThinkingBlockProps) {
  const [expanded, setExpanded] = useState(false)
  const isStreaming = status === 'thinking'

  return (
    <div className={cn('flex flex-col mt-3 w-full', className)}>
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors w-fit outline-none focus-visible:ring-2 focus-visible:ring-gray-300 rounded"
        aria-expanded={expanded}
      >
        <Brain size={13} className={cn(isStreaming && 'animate-pulse')} />
        <span>{isStreaming ? '正在思考中...' : '已完成思考'}</span>
        <ChevronDown
          size={12}
          className={cn('transition-transform', expanded && 'rotate-180')}
        />
      </button>

      {expanded && content && (
        <div className="mt-2 ml-1 pl-3 border-l-2 border-gray-200">
          <pre className="text-xs text-gray-400 whitespace-pre-wrap wrap-break-word font-mono leading-relaxed">
            {content}
            {isStreaming && (
              <span className="inline-block w-1 h-3 ml-0.5 bg-gray-400 animate-pulse align-middle" />
            )}
          </pre>
        </div>
      )}
    </div>
  )
}
