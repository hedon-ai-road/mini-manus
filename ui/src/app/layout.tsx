import type { Metadata } from "next";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: "MiniManus",
  description: 'MiniManus 是一个行动引擎，它超越了答案的范畴，可以执行任务、自动化工作流程，并扩展您的能力。',
  icons: {
    icon: '/icon.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN" className={cn("font-sans", geist.variable)}
    >
      <body>{children}</body>
    </html>
  );
}
