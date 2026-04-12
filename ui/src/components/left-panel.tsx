'use client'

import { MessageSquareText, MoreHorizontal, Plus, Trash } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import { Avatar, AvatarGroupCount } from "./ui/avatar"
import { Button } from "./ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "./ui/dropdown-menu"
import { Item, ItemActions, ItemContent, ItemDescription, ItemGroup, ItemMedia, ItemTitle } from "./ui/item"
import { Kbd, KbdGroup } from "./ui/kbd"
import { Sidebar, SidebarContent, SidebarHeader, SidebarTrigger } from "./ui/sidebar"

export function LeftPanel() {
    const router = useRouter()
    const params = useParams()
    const sessions = [
        "1", "2", "3"
    ]

    return (
        <Sidebar>
            {/* 顶部的切换按钮 */}
            <SidebarHeader>
                <SidebarTrigger className="cursor-pointer" />
            </SidebarHeader>
            {/* 中间内容 */}
            <SidebarContent className="p-2">
                {/* 新建任务 */}
                <Button
                    variant="outline"
                    className="cursor-pointer mb-3"
                    onClick={() => router.push('/')}
                >
                    <Plus />
                    新建任务
                    <KbdGroup>
                        <Kbd>⌘</Kbd>
                        <Kbd>K</Kbd>
                    </KbdGroup>
                </Button>
                {/* 会话列表 */}
                <ItemGroup className="gap-1">
                    {sessions.map((session) => (
                        <Item
                            key={session}
                            className={`p-2 hover:bg-white cursor-pointer gap-2 ${session == params.id ? "bg-white" : ''}`}
                            onClick={() => router.push(`/sessions/${session}`)}
                        >
                            {/* 左侧图标 */}
                            <ItemMedia>
                                <Avatar className="size-8">
                                    <AvatarGroupCount>
                                        <MessageSquareText/>
                                    </AvatarGroupCount>
                                </Avatar>
                            </ItemMedia>
                            {/* 中间内容 */}
                            <ItemContent className="gap-0">
                                <ItemTitle className="text-md font-medium line-clamp-1">图片合并为PDF的操作计划</ItemTitle>
                                <ItemDescription
                                    className="text-xs line-clamp-1"
                                >
                                    将多张图片合并为PDF，并优化PDF文件的排版和格式。
                                </ItemDescription>
                            </ItemContent>
                            {/* 右侧操作区 */}
                            <ItemActions className="flex flex-col pt-1 gap-0">
                                <ItemDescription className="text-xs">周一</ItemDescription>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button size="icon-xs" variant="ghost" className="cursor-pointer">
                                            <MoreHorizontal />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="center" side="bottom">
                                        <DropdownMenuItem variant="destructive" className="cursor-pointer">
                                            <Trash/>
                                            删除
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </ItemActions>
                        </Item>
                    ))}
                </ItemGroup>
            </SidebarContent>
        </Sidebar>
    )
}