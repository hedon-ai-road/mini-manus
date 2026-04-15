'use client'

import RFB from '@novnc/novnc/lib/rfb'
import { useEffect, useRef } from "react"
    
interface VNCViewerProps {
  url: string
  viewOnly?: boolean
}

export function VncViewer({ url, viewOnly }: VNCViewerProps) {
    const displayRef = useRef(null)
    useEffect(() => {
        // 1. 检查引用是否存在
        if (!displayRef.current) return

        // 2. 创建代理连接
        const rfb = new RFB(displayRef.current, url, {
            credentials: {
                password: '',
                username: '',
                target: '',
            }
        })

        // 3. 配置基础属性
        rfb.viewOnly = viewOnly || false
        rfb.scaleViewport = true
        rfb.background = '#000'
        rfb.addEventListener('connect', () => {
            console.log('连接成功')
        })
        rfb.addEventListener('disconnect', () => {
            console.log('连接失败')
        })
        rfb.addEventListener('error', (event) => {
            console.log('连接错误', event)
        })
        rfb.addEventListener('key', (event) => {
            console.log('键盘事件', event)
        })
        rfb.addEventListener('mouse', (event) => {
            console.log('鼠标事件', event)
        })
        rfb.addEventListener('clipboard', (event) => {
            console.log('剪贴板事件', event)
        })
        return () => rfb.disconnect()
    }, [url, viewOnly])
    return (
        <div
            ref={displayRef}
            style={{width: '100%', height: '100vh', background: '#000'}}
        />
    )
}