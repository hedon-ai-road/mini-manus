'use client'

import { Gift, Languages, LayoutGrid, Settings } from "lucide-react"
import { useState } from "react"
import { Button } from "./ui/button"
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Separator } from "./ui/separator"

export function ManusSettings() {
    const [activatedSetting, setActiveSetting] = useState<string>('common-setting')
    const settingMenus = [
        { key: 'common-setting', icon: Settings, title: '通用配置', childComponent: null },
        { key: 'llm-setting', icon: Languages, title: '模型提供商', childComponent: null },
        { key: 'a2a-setting', icon: LayoutGrid, title: 'A2A Agent 配置', childComponent: null },
        { key: 'mcp-setting', icon: Gift, title: 'MCP 服务器', childComponent: null },
    ]

    return (
        <Dialog>
            {/* 模态窗触发器 */}
            <DialogTrigger asChild>
                <Button variant="outline" size="icon-sm" className="cursor-pointer">
                    <Settings/>
                </Button>
            </DialogTrigger>
            {/* 模态窗本身 */}
            <DialogContent className="max-w-212.5!">
                {/* 模态窗 header */}
                <DialogHeader className="border-b pb-4">
                    <DialogTitle className="text-gray-700">MiniManus 设置</DialogTitle>
                    <DialogDescription className="text-gray-500">在此管理您的 MiniManus 设置</DialogDescription>
                </DialogHeader>
                {/* 模态窗中间内容 */}
                <div className="flex flex-row gap-4">
                    {/* 左侧快捷菜单 */}
                    <div className="max-w-45">
                        <div className="flex flex-col gap-0">
                            {settingMenus.map((setting) => (
                                <Button
                                    variant={ activatedSetting == setting.key ? 'default' : 'ghost'}
                                    key={setting.key}
                                    className="cursor-pointer justify-start"
                                    onClick={() => setActiveSetting(setting.key)}
                                >
                                    <setting.icon/>
                                    {setting.title}
                                </Button>
                            ))}
                        </div>
                    </div>
                    {/* 分隔符 */}
                    <Separator orientation="vertical"/>
                    {/* 右侧表单内容 */}
                    <div className="flex-1 h-125 scrollbar-hide overflow-y-auto">
                        {activatedSetting}
                    </div>
                </div>
                {/* 模态窗 footer */}
                <DialogFooter className="broder-t pt-4">
                    <DialogClose asChild>
                        <Button variant="outline" className="cursor-pointer">取消</Button>
                    </DialogClose>
                    <Button className="cursor-pointer">保存</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}