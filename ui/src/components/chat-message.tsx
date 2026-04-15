'use client'

import { cn } from "@/lib/utils"
import { Languages } from "lucide-react"
import { ManusIcon } from "./manus-icon"
import { MarkdownContent } from "./markdown-content"
import { ToolUse } from "./tool-use"


export interface ChatMessageProps {
    className?: string
    message: {
        type: string
        role?: string
    }
}

export function ChatMessage({ className, message }: ChatMessageProps) {
    const content = `## Python 冒泡排序

下面是一个**简洁**的实现，时间复杂度为 O(n²)，适合教学与小数据量场景。

### 要点

- 外层循环控制轮数，内层两两比较并交换
- 若某一轮没有交换，说明已有序，可**提前结束**

> 若需要稳定且更快的排序，可改用 \`sorted()\` 或归并排序。
`

    if (message.type === "user") {
        return (
            <div
                className={cn(
                    'flex w-full flex-col items-end justify-end gap-1 group mt-3',
                    className
                )}
            >
                {/* 顶部时间 */}
                <div className="flex items-end">
                    <div className="flex items-center justify-end gap-1 invisible group-hover:visible">
                        <div className="float-right transition text-xs text-gray-500 invisible group-hover:visible">
                            2个月前
                        </div>
                    </div>
                </div>
                {/* 底部用户消息 */}
                <div className="flex max-w-[90%] relative flex-col gap-2 items-end">
                    <div className="text-gray-700 relative flex items-center rounded-lg overflow-hidden bg-white p-3 border">
                        帮我写一个 Python 版本的冒泡排序
                    </div>
                </div>
            </div>
        )
    } else if (message.type === "assistant") {
        return (
            <div className={cn('flex flex-col gap-2 w-full group mt-3', className)}>
                <div className="flex items-center justify-between h-7 group">
                    <div className="flex items-center justify-center gap-1 text-gray-700">
                        <Languages size={18} />
                        <ManusIcon />
                    </div>
                </div>
                <div className="max-w-none p-0 m-0 text-gray-700">
                    <MarkdownContent content={content} />
                </div>
            </div>
        )
    } else if (message.type === "tool") {
        return (
            <ToolUse/>
        )
    } else if (message.type === "step") {
        return (
            <div> 步骤消息</div>
        )
    } else if (message.type === "attachments") {
        return (
            <div> 附件消息</div>
        )
    } else if (message.type === "error") {
        return (
            <div> 错误消息</div>
        )
    }
}