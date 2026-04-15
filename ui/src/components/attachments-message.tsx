'use client'

import { cn } from "@/lib/utils"
import { Eye, FileSearch, FileText } from "lucide-react"
import { Avatar, AvatarGroupCount } from "./ui/avatar"
import { Button } from "./ui/button"
import { Item, ItemActions, ItemContent, ItemDescription, ItemMedia, ItemTitle } from "./ui/item"

export interface AttachmentsMessageProps {
  className?: string
  role: string
}

export function AttachmentsMessage({ className, role }: AttachmentsMessageProps) {
    const files = [
        { "id": 1, "extension": "pdf", "filename": "go+java1.pdf", "size": "2.52MB" },
        { "id": 2, "extension": "pdf", "filename": "go+java2.pdf", "size": "2.52MB" },
        { "id": 3, "extension": "pdf", "filename": "go+java3.pdf", "size": "2.52MB" },
        { "id": 4, "extension": "pdf", "filename": "go+java4.pdf", "size": "2.52MB" },
    ]

    if (role === 'user') {
        return (
            <div
                className={cn(
                'flex flex-col flex-wrap gap-2 items-end justify-end',
                className
                )}
            >
                <div className="flex gap-2 flex-wrap max-w-[568px] justify-end">
                    {files.map((file, index) => (
                        <Item
                            key={file.id}
                            variant="outline"
                            className="w-[280px] bg-white flex-shrink-0 p-2 gap-2"
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
                                    <Eye/>
                                </Button>
                            </ItemActions>
                        </Item>
                    ))}
                </div>
            </div>
        )
    } else if (role === 'assistant') {
        return (
            <div
                className={cn(
                'flex flex-col flex-wrap gap-2 justify-start',
                className
                )}
            >
                <div className="flex gap-2 flex-wrap max-w-[568px]">
                    {files.map((file) => (
                        <Item
                            key={file.id}
                            variant="outline"
                            className="w-[280px] bg-white flex-shrink-0 p-2 gap-2"
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
                                    <Eye/>
                                </Button>
                            </ItemActions>
                        </Item>
                    ))}
                    <Button variant="outline" className="cursor-pointer">
                        <FileSearch size={16} />
                        <span className="text-xs text-gray-700">查看此任务中所有的文件</span>
                    </Button>
                </div>
            </div>
        )
    }
}