'use client'

import { VncViewer } from "@/components/vnc-viewer"

export default function Page() {
    return (
        <div className="w-screen h-screen">
            <VncViewer url="ws://127.0.0.1:5901" viewOnly={false} />
        </div>
    )
}