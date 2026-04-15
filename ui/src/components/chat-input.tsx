'use client'

import { cn } from "@/lib/utils";
import { ArrowUp, FileText, Paperclip, XCircle } from "lucide-react";
import { Avatar, AvatarGroupCount } from "./ui/avatar";
import { Button } from "./ui/button";
import { Item, ItemActions, ItemContent, ItemDescription, ItemMedia, ItemTitle } from "./ui/item";
import { ScrollArea, ScrollBar } from "./ui/scroll-area";

interface ChatInputProps {
    className?: string;
}

export function ChatInput({ className }: ChatInputProps) {
    const files = [
        { "id": 1, "extension": "pdf", "filename": "go+java1.pdf", "size": "2.52MB" },
        { "id": 2, "extension": "pdf", "filename": "go+java2.pdf", "size": "2.52MB" },
        { "id": 3, "extension": "pdf", "filename": "go+java3.pdf", "size": "2.52MB" },
        { "id": 4, "extension": "pdf", "filename": "go+java4.pdf", "size": "2.52MB" },
    ]

    return (
        <div className={cn("flex flex-col bg-white w-full rounded-2xl py-3 border", className)}>
            {/* 顶部的文件列表 */}
            <div className="w-full px-4 mb-1">
                <ScrollArea className="w-full whitespace-nowrap">
                    <div className="flex w-max min-w-0 gap-4 pb-1">
                        {files.map((file) => (
                            <Item
                                key={file.id}
                                variant="muted"
                                className="w-auto shrink-0 p-2 gap-2"
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
                                        <XCircle/>
                                    </Button>
                                </ItemActions>
                            </Item>
                        ))}
                    </div>
                    <ScrollBar orientation="horizontal" />
                </ScrollArea>
            </div>
            {/* 中间输入框 */}
            <div className="px-4 mb-3">
                <textarea
                    rows={2}
                    placeholder="Ask anything..."
                    className="scrollbar-hide outline-none w-full text-sm resize-none h-[46px] min-h-[40px]"
                />
            </div>
            {/* 底部上传&发送按钮 */}
            <footer className="flex flex-row justify-between w-full px-3">
                {/* 上传按钮 */}
                <div className="flex gap-2">
                    <Button variant="outline" className="rounded-full w-8 h-8 cursor-pointer">
                        <Paperclip/>
                    </Button>
                </div>
                {/* 发送/暂停按钮 */}
                <div className="flex gap-2">
                    <Button variant="outline" className="rounded-full w-8 h-8 cursor-pointer">
                        <ArrowUp/>
                    </Button>
                </div>
            </footer>
        </div>
    )
}