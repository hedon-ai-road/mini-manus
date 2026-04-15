'use client'

import { ChatHeader } from "@/components/chat-header";
import { ChatInput } from "@/components/chat-input";
import { SuggestedQuestions } from "@/components/suggested-questions";

export default function Page() {
  return (
    <div className="h-full flex flex-col">
      {/* 顶部 header */}
      <ChatHeader/>
      {/* 中间对话框 */}
      <div className="relative w-full max-w-full sm:max-w-3xl sm:min-w-[97.5] px-4 mx-auto mt-[20vh]">
        {/* 对话提示内容 */}
        <div className="flex-1 text-[32px] font-bold mb-4">
          <div className="text-gray-700">Hello</div>
          <div className="text-gray-500">How can I help you?</div>
        </div>
        {/* 对话框 */}
        <ChatInput className="mb-4"/>
        {/* 推荐对话内容 */}
        <SuggestedQuestions className="mb-4"/>
      </div>
    </div>
  );
}
