'use client'

import { ChatHeader } from "@/components/chat-header";

export default function Page() {
  return (
    <div className="h-full flex flex-col">
      {/* 顶部 header */}
      <ChatHeader/>
      {/* 中间对话框 - 垂直居中，视觉上移一个导航栏高度 */}
    </div>
  );
}
