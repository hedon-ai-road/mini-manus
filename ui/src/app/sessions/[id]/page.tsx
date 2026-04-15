import { ChatInput } from "@/components/chat-input"
import { PlanPanel } from "@/components/plan-panel"
import { SessionHeader } from "@/components/session-header"

// 定义页面路由参数
interface PageProps{
    params: Promise<{ id: string }>
}

export default async function Page(
    {params}: PageProps,
) {
    // 从 params 中取出 id
    const { id } = await params
    return (
        <div className="relative flex flex-col h-full flex-1 min-w-0 px-4">
            {/* 顶部标题 & 操作按钮 */}
            <SessionHeader/>
            {/* 中间内容 */}
            <div className="mx-auto w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] flex flex-col flex-1">
                <div className="pb-10">
                    中间对话内容列表
                </div>
                {/* 底部输入框 & 任务清单 */}
                <div className="sticky bottom-0 mt-auto">
                    {/* 规划列表 */}
                    <PlanPanel className="mb-2"/>
                    {/* 输入框 */}
                    <ChatInput className="mb-4"/>
                </div>
            </div>
        </div>
    )
}