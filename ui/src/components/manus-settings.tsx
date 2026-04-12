'use client'

import { Gift, Languages, LayoutGrid, LayoutList, Settings, Trash, Wrench } from "lucide-react"
import { useState } from "react"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Field, FieldDescription, FieldGroup, FieldLabel, FieldLegend, FieldSet } from "./ui/field"
import { Input } from "./ui/input"
import { Item, ItemContent, ItemDescription, ItemGroup, ItemTitle } from "./ui/item"
import { Kbd } from "./ui/kbd"
import { Separator } from "./ui/separator"
import { Switch } from "./ui/switch"
import { Textarea } from "./ui/textarea"

export function CommonSetting() {
    return (
        <form className="w-full px-1">
            <FieldGroup>
                <FieldSet>
                    {/* 顶部表单标题 */}
                    <FieldLegend className="text-lg font-bold text-gray-700">通用配置</FieldLegend>
                    <FieldDescription className="text-sm">
                        配置 MinuManus 的通用配置信息
                    </FieldDescription>
                    {/* 中间表单内容 */}
                    <FieldGroup>
                        <Field>
                            <FieldLabel htmlFor="max_iterations">
                                最大迭代次数
                                <Kbd>max_iterations</Kbd>
                            </FieldLabel>
                            <Input
                                id="max_iterations"
                                type="number"
                                placeholder="Agent 最大迭代次数"
                                defaultValue={100}
                                min={0}
                                max={200}
                                required
                            />
                            <FieldDescription className="text-xs">执行 Agent 最大能迭代调用工具的次数，默认为 100</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="max_retries">
                                最大重试次数
                                <Kbd>max_retries</Kbd>
                            </FieldLabel>
                            <Input
                                id="max_retries"
                                type="number"
                                placeholder="Tool 最大重试次数"
                                defaultValue={3}
                                min={0}
                                max={10}
                                required
                            />
                            <FieldDescription className="text-xs">执行 Agent 调用工具失败后，最大能重试的次数，默认为 3</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="max_search_results">
                                最大搜索结果数
                                <Kbd>max_search_results</Kbd>
                            </FieldLabel>
                            <Input
                                id="max_search_results"
                                type="number"
                                placeholder="搜索工具返回的结果数"
                                defaultValue={10}
                                min={0}
                                max={30}
                                required
                            />
                            <FieldDescription className="text-xs">搜索工具返回的结果数，默认为 10</FieldDescription>
                        </Field>
                    </FieldGroup>
                </FieldSet>
            </FieldGroup>
        </form>
    )
}

export function LLMSetting() {
    return (
        <form className="w-full px-1">
            <FieldGroup>
                <FieldSet>
                    {/* 顶部表单标题 */}
                    <FieldLegend className="text-lg font-bold text-gray-700">模型提供商</FieldLegend>
                    <FieldDescription className="text-sm">
                        配置 Agent 使用的基础 LLM 模型（兼容 OpenAI 格式）
                    </FieldDescription>
                    {/* 中间表单内容 */}
                    <FieldGroup>
                        <Field>
                            <FieldLabel htmlFor="base_url">
                                提供商基础地址
                                <Kbd>base_url</Kbd>
                            </FieldLabel>
                            <Input
                                id="base_url"
                                type="url"
                                placeholder="提供商基础地址"
                                defaultValue="https://api.deepseek.com"
                                required
                            />
                            <FieldDescription className="text-xs">提供商的基础地址，默认为 deepseek 的默认地址</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="api_key">
                                提供商密钥
                                <Kbd>api_key</Kbd>
                            </FieldLabel>
                            <Input
                                id="api_key"
                                type="text"
                                placeholder="提供商 API 密钥"
                                defaultValue=""
                                required
                            />
                            <FieldDescription className="text-xs">提供商的 API 密钥</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="model_name">
                                模型名称
                                <Kbd>model_name</Kbd>
                            </FieldLabel>
                            <Input
                                id="model_name"
                                type="text"
                                placeholder="模型名称"
                                defaultValue="deepseek-chat"
                                required
                            />
                            <FieldDescription className="text-xs">模型名称，默认为 deepseek-chat</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="temperature">
                                温度
                                <Kbd>temperature</Kbd>
                            </FieldLabel>
                            <Input
                                id="temperature"
                                type="number"
                                placeholder="模型温度"
                                defaultValue={0.7}
                                min={0}
                                max={2}
                                step={0.1}
                                required
                            />
                            <FieldDescription className="text-xs">模型温度，默认为 0.7</FieldDescription>
                        </Field>
                        <Field>
                            <FieldLabel htmlFor="max_tokens">
                                最大 Token 数
                                <Kbd>max_token</Kbd>
                            </FieldLabel>
                            <Input
                                id="max_tokens"
                                type="number"
                                placeholder="模型最大 Token 数"
                                defaultValue={8192}
                                min={1}
                                max={128000}
                                required
                            />
                            <FieldDescription className="text-xs">模型单次回复允许输出的最大 Token 数，默认为 8192</FieldDescription>
                        </Field>
                    </FieldGroup>
                </FieldSet>
            </FieldGroup>
        </form>
    )
}

export function A2ASetting() {
    return (
        <div className="w-full px-1">
            <FieldGroup>
                <FieldSet>
                    {/* 顶部标题 */}
                    <FieldLegend className="w-full flex justify-between items-center text-lg font-bold text-gray-700">
                        A2A Agent 配置
                        <Dialog>
                            {/* 模态窗触发按钮*/}
                            <DialogTrigger asChild>
                                <Button type="button" size="xs" className="cursor-pointer">新增远程 Agent</Button>
                            </DialogTrigger>
                            {/* 新增 A2A 服务器模态窗*/}
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle className="text-gray-700">新增远程 Agent</DialogTitle>
                                    <DialogDescription className="text-gray-500">
                                        MinuManus 使用标准的 A2A 协议来连接远程 Agent。
                                        <br />
                                        请将您的配置粘贴到下方，然后点击“添加”即可。
                                    </DialogDescription>
                                </DialogHeader>
                                <form className="w-full">
                                    <FieldGroup>
                                        <FieldSet>
                                            <Field>
                                                <Input
                                                    id="base_url"
                                                    type="url"
                                                    placeholder="Example: http://example.com/a2a"
                                                    required
                                                />
                                            </Field>
                                        </FieldSet>
                                    </FieldGroup>
                                </form>
                                <DialogFooter>
                                    <DialogClose asChild>
                                        <Button variant="outline" className="cursor-pointer">取消</Button>
                                    </DialogClose>
                                    <Button className="cursor-pointer">添加</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </FieldLegend>
                    {/* 描述信息 */}
                    <FieldDescription className="text-sm text-gray-500">
                        模拟 A2A 协议（Agent to Agent Protocal）通过集成外部 Agent 来增强 MinuManus。
                    </FieldDescription>
                    {/* 中间列表内容 */}
                    <ItemGroup>
                        <Item variant="outline">
                            <ItemContent>
                                <ItemTitle className="w-full flex justify-between items-center text-md font-bold text-gray-700">
                                    {/* 左侧 Agent 名称 */}
                                    <div className="flex gap-2 items-center">
                                        天气Agent
                                        <Badge>禁用</Badge>
                                    </div>
                                    {/* 右侧基础操作 */}
                                    <div className="flex items-center justify-center gap-2">
                                        <Button type="button" variant="ghost" size="icon-xs" className="cursor-pointer">
                                            <Trash/>
                                        </Button>
                                        <Switch/>
                                    </div>
                                </ItemTitle>
                                <ItemDescription>
                                    提供天气查询相关功能
                                </ItemDescription>
                                <ItemDescription className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500">
                                    <LayoutList size={12} />
                                    <Badge variant="secondary" className="text-gray-500">输入: text</Badge>
                                    <Badge variant="secondary" className="text-gray-500">输出: text</Badge>
                                    <Badge variant="secondary" className="text-gray-500">流式输出</Badge>
                                    <Badge variant="secondary" className="text-gray-500">推送通知</Badge>
                                </ItemDescription>
                            </ItemContent>
                        </Item>
                    </ItemGroup>
                </FieldSet>
            </FieldGroup>
        </div>
    )
}

export function MCPSetting() {
    const mcpConfigPlaceholder = `{
        "mcpServers": {
            "qiniu": {
            "command": "uvx",
            "args": [
                "qiniu-mcp-server"
            ],
            "env": {
                "QINIU_ACCESS_KEY": "YOUR_ACCESS_KEY",
                "QINIU_SECRET_KEY": "YOUR_SECRET_KEY"
            }
            }
        }
    }`

    return (
        <div className="w-full px-1">
            <FieldGroup>
                <FieldSet>
                    {/* 顶部标题 */}
                    <FieldLegend className="w-full flex justify-between items-center text-lg font-bold text-gray-700">
                        MCP 服务器配置
                        <Dialog>
                            {/* 模态窗触发按钮*/}
                            <DialogTrigger asChild>
                                <Button type="button" size="xs" className="cursor-pointer">新增 MCP</Button>
                            </DialogTrigger>
                            {/* 新增 MCP 服务器模态窗*/}
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle className="text-gray-700">新增 MCP</DialogTitle>
                                    <DialogDescription className="text-gray-500">
                                        MinuManus 使用标准的 MCP 协议来连接 MCP 服务器。
                                        <br />
                                        请将您的配置粘贴到下方，然后点击“添加”即可添加 MCP 服务器。
                                    </DialogDescription>
                                </DialogHeader>
                                <form className="w-full">
                                    <FieldGroup>
                                        <FieldSet>
                                            <Field>
                                                <Textarea
                                                    id="mcp_config"
                                                    placeholder={mcpConfigPlaceholder}
                                                    required
                                                />
                                            </Field>
                                        </FieldSet>
                                    </FieldGroup>
                                </form>
                                <DialogFooter>
                                    <DialogClose asChild>
                                        <Button variant="outline" className="cursor-pointer">取消</Button>
                                    </DialogClose>
                                    <Button className="cursor-pointer">添加</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </FieldLegend>
                    {/* 描述信息 */}
                    <FieldDescription className="text-sm text-gray-500">
                        模拟 MCP 协议（Model Context Protocol）通过集成外部 MCP 服务器来增强 MinuManus。
                    </FieldDescription>
                    {/* 中间列表内容 */}
                    <ItemGroup>
                        <Item variant="outline">
                            <ItemContent>
                                <ItemTitle className="w-full flex justify-between items-center text-md font-bold text-gray-700">
                                    {/* 左侧 MCP 服务器名称 */}
                                    <div className="flex gap-2 items-center">
                                        bilibili-video-info-mcp
                                        <Badge>stdio</Badge>
                                        <Badge>禁用</Badge>
                                    </div>
                                    {/* 右侧基础操作 */}
                                    <div className="flex items-center justify-center gap-2">
                                        <Button type="button" variant="ghost" size="icon-xs" className="cursor-pointer">
                                            <Trash/>
                                        </Button>
                                        <Switch/>
                                    </div>
                                </ItemTitle>
                                <ItemDescription className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500">
                                    <Wrench size={12} />
                                    <Badge variant="secondary" className="text-gray-500">get_sub_title</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_danmuku</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_comments</Badge>
                                    <Badge variant="secondary" className="text-gray-500">version</Badge>
                                    <Badge variant="secondary" className="text-gray-500">list_buckets</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_object</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_object_info</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_object_info</Badge>
                                    <Badge variant="secondary" className="text-gray-500">get_object_info</Badge>
                                </ItemDescription>
                            </ItemContent>
                        </Item>
                    </ItemGroup>
                </FieldSet>
            </FieldGroup>
        </div>
    )
}

export function ManusSettings() {
    const [activatedSetting, setActiveSetting] = useState<string>('common-setting')
    const settingMenus = [
        { key: 'common-setting', icon: Settings, title: '通用配置', childComponent: CommonSetting },
        { key: 'llm-setting', icon: Languages, title: '模型提供商', childComponent: LLMSetting },
        { key: 'a2a-setting', icon: LayoutGrid, title: 'A2A Agent 配置', childComponent: A2ASetting },
        { key: 'mcp-setting', icon: Gift, title: 'MCP 服务器', childComponent: MCPSetting },
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
                        {activatedSetting === 'common-setting' && <CommonSetting />}
                        {activatedSetting === 'llm-setting' && <LLMSetting />}
                        {activatedSetting === 'a2a-setting' && <A2ASetting />}
                        {activatedSetting === 'mcp-setting' && <MCPSetting />}
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