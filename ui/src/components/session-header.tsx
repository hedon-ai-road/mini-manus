'use client'

import { Download, FileSearchCorner, FileText } from "lucide-react"
import { Avatar, AvatarGroupCount } from "./ui/avatar"
import { Button } from "./ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Item, ItemActions, ItemContent, ItemDescription, ItemMedia, ItemTitle } from "./ui/item"
import { ScrollArea } from "./ui/scroll-area"
import { SidebarTrigger, useSidebar } from "./ui/sidebar"

export function SessionHeader() {
    const { open, isMobile } = useSidebar()
    const files = [
        { "id": 1, "extension": "pdf", "filename": "go+java1.pdf", "size": "2.52MB" },
        { "id": 2, "extension": "pdf", "filename": "go+java2.pdf", "size": "2.52MB" },
        { "id": 3, "extension": "pdf", "filename": "go+java3.pdf", "size": "2.52MB" },
        { "id": 4, "extension": "pdf", "filename": "go+java4.pdf", "size": "2.52MB" },
        { "id": 5, "extension": "pdf", "filename": "go+java5.pdf", "size": "2.52MB" },
        { "id": 6, "extension": "pdf", "filename": "go+java6.pdf", "size": "2.52MB" },
        { "id": 7, "extension": "pdf", "filename": "go+java7.pdf", "size": "2.52MB" },
        { "id": 8, "extension": "pdf", "filename": "go+java8.pdf", "size": "2.52MB" },
        { "id": 9, "extension": "pdf", "filename": "go+java9.pdf", "size": "2.52MB" },
        { "id": 10, "extension": "pdf", "filename": "go+java10.pdf", "size": "2.52MB" },
    ]

    return (
        <header className="bg-[#f8f8f7] flex flex-row items-center justify-between pt-3 pb-2 gap-2 sticky top-0 z-10 flex-shrink-0">
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
                <Dialog>
                    {/* 模态窗触发器 */}
                    <DialogTrigger asChild>
                        <Button variant="ghost" size="icon-sm" className="cursor-pointer">
                            <FileSearchCorner/>
                        </Button>
                    </DialogTrigger>
                    {/* 模态窗内容 */}
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>此任务中的所有文件</DialogTitle>
                        </DialogHeader>
                        <ScrollArea className="h-[500px]">
                            <div className="flex flex-col gap-1">
                                {files.map((file) => (
                                    <Item
                                        key={file.id}
                                        variant="default"
                                        className="flex-shrink-0 p-2 gap-2 cursor-pointer hover:bg-gray-100"
                                    >
                                        {/* 左侧文件图片 */}
                                        <ItemMedia>
                                            <Avatar className="size-8">
                                                <AvatarGroupCount>
                                                    <FileText/>
                                                </AvatarGroupCount>
                                            </Avatar>
                                        </ItemMedia>
                                        {/* 文件信息 */}
                                        <ItemContent className="gap-0">
                                            <ItemTitle className="text-sm text-gray-700">{file.filename}</ItemTitle>
                                            <ItemDescription className="text-ms">
                                                {file.extension} · {file.size}
                                            </ItemDescription>
                                        </ItemContent>
                                        {/* 右侧操作区 */}
                                        <ItemActions>
                                            <Button variant="ghost" size="icon-xs" className="cursor-pointer">
                                                <Download/>
                                            </Button>
                                        </ItemActions>
                                    </Item>
                                ))}
                            </div>
                        </ScrollArea>
                    </DialogContent>
                </Dialog>

            </div>
            {/* 右侧占位 */}
            <div className="flex-1"></div>
        </header>
    )
}