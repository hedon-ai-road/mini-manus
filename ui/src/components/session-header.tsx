'use client'

import { FileSearchCorner } from "lucide-react"
import { Button } from "./ui/button"
import { SidebarTrigger, useSidebar } from "./ui/sidebar"

export function SessionHeader() {
    const {open, isMobile} = useSidebar()

    return (
        <header className="bg-[#f8f8f7] sm:min-w-97.5 flex flex-row items-center justify-between pt-3 pb-2 gap-2 sticky top-0 z-10 flex-shrink-0">
            {/* 左侧操作按钮 */}
            <div className="flex items-center flex-1">
                <div className="relative flex items-center">
                    {(!open || isMobile) && <SidebarTrigger className="cursor-pointer flex-shrink-0"/>}
                </div>
            </div>
            {/* 中间会话标题区 */}
            <div className="text-gray-700 max-w-full sm:max-w-3xl sm:min-w-97.5 flex w-full items-center justify-between gap-1 overflow-hidden">
                {/* 左侧标题 */}
                <div className="text-lg whitespace-nowrap text-ellipsis overflow-hidden">
                    编写 Python 冒泡排序算法
                </div>
                {/* 右侧操作按钮 */}
                <Button variant="ghost" size="icon-sm" className="cursor-pointer">
                    <FileSearchCorner/>
                </Button>
            </div>
            {/* 右侧占位 */}
            <div className="flex-1"></div>
        </header>
    )
}