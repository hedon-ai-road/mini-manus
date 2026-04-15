'use client'

import { cn } from "@/lib/utils"
import { Check, ChevronDown, ChevronUp, Clock } from "lucide-react"
import { useState } from "react"
import { Button } from "./ui/button"

export interface PlanPanelProps {
  className?: string
}

export function PlanPanel({ className }: PlanPanelProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const togglePanel = () => setIsExpanded(!isExpanded)
    const steps = [
        {
            id: 1,
            status: "completed",
            description: "1.将多张图片合并为PDF，并优化PDF文件的排版和格式。"
        },
        {
            id: 2,
            status: "pending",
            description: "2.将多张图片合并为PDF，并优化PDF文件的排版和格式。"
        },
        {
            id: 3,
            status: "pending",
            description: "3.将多张图片合并为PDF，并优化PDF文件的排版和格式。"
        },
        {
            id: 4,
            status: "pending",
            description: "4.将多张图片合并为PDF，并优化PDF文件的排版和格式。"
        },
        {
            id: 5,
            status: "pending",
            description: "5.将多张图片合并为PDF，并优化PDF文件的排版和格式。"
        },
    ]

    return (
        <div className={cn('bg-white rounded-xl border', className)}>
            {/* 折叠状态 */}
            {!isExpanded && <div
                className="flex flex-row items-start justify-between pr-3 relative clickable cursor-pointer rounded-xl z-99"
                onClick={togglePanel}
            >
                {/* 左侧的最新计划 */}
                <div className="flex-1 min-w-0 relative overflow-hidden">
                    <div className="w-full h-9">
                        <div className="flex items-center justify-center gap-2.5 w-full px-4 py-2 truncate text-gray-500">
                        <Clock size={16} />
                        <div className="flex flex-col w-full gap-0.5 truncate">
                            <div className="text-sm truncate">
                                将多张图片合并为PDF，并优化PDF文件的排版和格式。
                            </div>
                        </div>
                        </div>
                    </div>
                </div>
                {/* 右侧操作按钮&步骤信息 */}
                <div className="flex h-full justify-center gap-2 flex-shrink-0 items-center py-2.5">
                <span className="text-xs text-gray-500">
                    1 / 5
                </span>
                <ChevronUp className="text-gray-700" size={16} />
                </div>
            </div>}
            {/* 展开状态 */}
            {isExpanded && (
                <div className="flex flex-col py-4 rounded-xl z-99">
                    {/* 顶部留白+按钮 */}
                    <div className="flex px-4 mb-4 w-full">
                        <div className="flex items-start ml-auto">
                            <div className="flex items-center justify-center gap-2">
                                <Button
                                onClick={togglePanel}
                                variant="ghost"
                                size="icon-xs"
                                className="cursor-pointer"
                                >
                                <ChevronDown className="text-gray-500" size={16} />
                                </Button>
                            </div>
                        </div>
                    </div>
                    {/* 底部计划列表 */}
                    <div className="px-4">
                        <div className="bg-gray-50 rounded-lg px-2 py-3">
                            {/* 任务进度信息 */}
                            <div className="flex justify-between w-full px-4">
                                <span className="text-gray-700 font-bold">任务进度</span>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-gray-500">
                                        1 / 5
                                    </span>
                                </div>
                            </div>
                            {/* 计划列表 */}
                            <div className="max-h-[min(calc(100vh-360px),400px)] overflow-y-auto">
                                {steps.map((step) => (
                                    <div key={step.id} className="flex items-center text-gray-500 text-sm gap-2.5 w-full px-4 py-2 truncate">
                                        {/* 任务状态图标 */}
                                        {step.status === "completed" ? (
                                            <Check size={16} className="relative top-0.5 flex-shrink-0" />
                                        ) : (
                                            <Clock size={16} className="relative top-0.5 flex-shrink-0" />
                                        )}
                                        {/* 任务描述 */}
                                        <div className="flex flex-col w-full truncate">
                                            <div className="text-sm truncate">{step.description}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}