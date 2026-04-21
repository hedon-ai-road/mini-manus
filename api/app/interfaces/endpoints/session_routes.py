import asyncio
import logging
import websockets
from websockets import ConnectionClosed
from typing import AsyncGenerator, Optional, Dict
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.application.errors.exceptions import NotFoundError
from app.application.services.agent_service import AgentService
from app.domain.models.session import SessionStatus
from app.interfaces.schemas import Response
from app.interfaces.schemas.event import EventMapper
from app.interfaces.schemas.session import (
    ChatRequest,
    CreateSessionResponse,
    FileReadRequest,
    FileReadResponse,
    ListSessionResponse,
    ListSessionItem,
    GetSessionResponse,
    GetSessionFilesResponse,
    ShellReadRequest,
    ShellReadResponse,
)
from app.interfaces.service_dependencies import get_agent_service, get_session_service
from app.application.services.session_service import SessionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["会话模块"])

# 流式获取会话详情睡眠间隔
SESSION_SLEEP_INTERVAL = 5

@router.post(
    path="",
    response_model=Response[CreateSessionResponse],
    summary="创建新任务会话",
    description="创建一个空白的新任务会话",
)
async def create_session(
        session_service: SessionService = Depends(get_session_service),
) -> Response[CreateSessionResponse]:
    """创建一个空白的新任务会话"""
    session = await session_service.create_session()
    return Response.success(
        msg="创建任务会话成功",
        data=CreateSessionResponse(session_id=session.id)
    )

@router.get(
    path="",
    response_model=Response[ListSessionResponse],
    summary="获取会话列表基础信息",
    description="获取MoocManus项目中所有任务会话基础信息列表",
)
async def get_all_sessions(
        session_service: SessionService = Depends(get_session_service),
) -> Response[ListSessionResponse]:
    """获取MoocManus项目中所有任务会话基础信息列表"""
    sessions = await session_service.get_all_sessions()
    session_items = [
        ListSessionItem(
            session_id=session.id,
            title=session.title,
            latest_message=session.latest_message,
            latest_message_at=session.latest_message_at,
            status=session.status,
            unread_message_count=session.unread_message_count,
        )
        for session in sessions
    ]
    return Response.success(
        msg="获取任务会话列表成功",
        data=ListSessionResponse(sessions=session_items)
    )


@router.post(
    path="/{session_id}/clear-unread-message-count",
    response_model=Response[Optional[Dict]],
    summary="清除指定任务会话未读消息数",
    description="清除指定任务会话未读消息数",
)
async def clear_unread_message_count(
        session_id: str,
        session_service: SessionService = Depends(get_session_service),
) -> Response[Optional[Dict]]:
    """根据传递的会话id清空未读消息数"""
    await session_service.clear_unread_message_count(session_id)
    return Response.success(msg="清除未读消息数成功")


@router.post(
    path="/{session_id}/delete",
    response_model=Response[Optional[Dict]],
    summary="删除指定任务会话",
    description="根据传递的会话id删除指定任务会话",
)
async def delete_session(
        session_id: str,
        session_service: SessionService = Depends(get_session_service),
) -> Response[Optional[Dict]]:
    """根据传递的会话id删除指定任务会话"""
    await session_service.delete_session(session_id)
    return Response.success(msg="删除任务会话成功")

@router.post(
    path="/{session_id}/chat",
    summary="向指定任务会话发起聊天请求",
    description="向指定任务会话发起聊天请求"
)
async def chat(
    session_id: str,
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    """根据传递的会话id+chat请求数据向指定会话发起聊天请求"""
    async def event_generator():
        # 调用Agent服务发起聊天
        async for event in agent_service.chat(
            session_id=session_id,
            message=request.message,
            attachments=request.attachments,
            latest_event_id=request.event_id,
            timestamp=request.timestamp,
        ):
            # 将 Agent 事件转换为 SSE 数据
            sse_event = EventMapper.event_to_sse_event(event)
            if sse_event:
                yield ServerSentEvent(
                    event=sse_event.event,
                    data=sse_event.data.model_dump_json(),
                )
    return EventSourceResponse(event_generator())

@router.get(
    path="/{session_id}",
    response_model=Response[GetSessionResponse],
    summary="获取指定会话详情信息",
    description="根据传递的会话id获取该会话的对话详情",
)
async def get_session(
        session_id: str,
        session_service: SessionService = Depends(get_session_service),
) -> Response[GetSessionResponse]:
    """传递指定会话id获取该会话的对话详情"""
    session = await session_service.get_session(session_id)
    if not session:
        raise NotFoundError("该会话不存在，请核实后重试")
    return Response.success(
        msg="获取会话详情成功",
        data=GetSessionResponse(
            session_id=session.id,
            title=session.title,
            status=session.status,
            events=EventMapper.events_to_sse_events(session.events),
        )
    )

@router.post(
    path="/stream",
    summary="流式获取所有会话基础信息列表",
    description="间隔指定时间流式获取所有会话基础信息列表",
)
async def stream_sessions(
        session_service: SessionService = Depends(get_session_service),
) -> EventSourceResponse:
    """间隔指定时间流式获取所有会话基础信息列表"""

    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        """定义一个异步迭代器，用于获取所有会话列表"""
        # 记录上一次推送时各 session 的状态，用于识别"刚变成 completed"的 session
        prev_status: dict[str, str] = {}
        first_push = True

        while True:
            sessions = await session_service.get_all_sessions()
            has_active = any(
                s.status in (SessionStatus.RUNNING, SessionStatus.WAITING)
                for s in sessions
            )

            if first_push:
                # 首次推送：全量，让前端拿到完整快照
                sessions_to_send = sessions
                first_push = False
            else:
                # 后续推送：只推 active session + 刚刚变成 completed 的 session
                # 这样前端既能看到状态变更，又不会重复传输无变化的历史数据
                sessions_to_send = [
                    s for s in sessions
                    if s.status in (SessionStatus.RUNNING, SessionStatus.WAITING)
                    or prev_status.get(s.id) in (SessionStatus.RUNNING, SessionStatus.WAITING)
                ]

            # 更新状态快照
            prev_status = {s.id: s.status for s in sessions}

            if sessions_to_send:
                session_items = [
                    ListSessionItem(
                        session_id=session.id,
                        title=session.title,
                        latest_message=session.latest_message,
                        latest_message_at=session.latest_message_at,
                        status=session.status,
                        unread_message_count=session.unread_message_count,
                    )
                    for session in sessions_to_send
                ]
                yield ServerSentEvent(
                    event="sessions",
                    data=ListSessionResponse(sessions=session_items).model_dump_json(),
                )

            if not has_active:
                # 无活跃任务，关闭流；前端收到流结束信号后可按需延迟重连
                return

            await asyncio.sleep(SESSION_SLEEP_INTERVAL)

    return EventSourceResponse(event_generator())


@router.post(
    path="/{session_id}/stop",
    response_model=Response[Optional[Dict]],
    summary="停止指定任务会话",
    description="根据传递的指定会话id停止对应任务会话",
)
async def stop_session(
        session_id: str,
        agent_service: AgentService = Depends(get_agent_service),
) -> Response[Optional[Dict]]:
    """根据传递的指定会话id停止对应任务会话"""
    await agent_service.stop_session(session_id)
    return Response.success(msg="停止任务会话成功")

@router.get(
    path="/{session_id}/files",
    response_model=Response[GetSessionFilesResponse],
    summary="获取指定任务会话文件列表信息",
    description="获取指定任务会话文件列表信息",
)
async def get_session_files(
        session_id: str,
        session_service: SessionService = Depends(get_session_service),
) -> Response[GetSessionFilesResponse]:
    """获取指定任务会话文件列表信息"""
    files = await session_service.get_session_files(session_id)
    return Response.success(
        msg="获取会话文件列表成功",
        data=GetSessionFilesResponse(files=files)
    )


@router.post(
    path="/{session_id}/file",
    response_model=Response[FileReadResponse],
    summary="查看会话沙箱中指定文件的内容",
    description="根据传递的会话id+文件路径查看沙箱中文件的内容信息"
)
async def read_file(
        session_id: str,
        request: FileReadRequest,
        session_service: SessionService = Depends(get_session_service),
) -> Response[FileReadResponse]:
    """根据传递的会话id+文件路径查看沙箱中文件的内容信息"""
    result = await session_service.read_file(session_id, request.filepath)
    return Response.success(
        msg="获取会话文件内容成功",
        data=result
    )

@router.post(
    path="/{session_id}/shell",
    response_model=Response[ShellReadResponse],
    summary="查看会话的shell内容输出",
    description="传递指定会话id与shell会话标识，查看shell内容输出",
)
async def read_shell_output(
        session_id: str,
        request: ShellReadRequest,
        session_service: SessionService = Depends(get_session_service),
) -> Response[ShellReadResponse]:
    """查看会话的shell内容输出"""
    result = await session_service.read_shell_output(session_id, request.session_id)
    return Response.success(
        msg="获取Shell内容输出结果成功",
        data=result,
    )

@router.websocket(
    path="/{session_id}/vnc",
)
async def vnc_websocket(
    websocket: WebSocket,
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> None:
    """VNC Websocket端点，用于建立与沙箱环境的vnc连接，并双向转发数据"""
    # 从客户端 noVNC 接收子协议
    protocols_str = websocket.headers.get("sec-websocket-protocol", "")
    protocols = [p.strip() for p in protocols_str.split(",") if p.strip()]

    # 判断使用不同协议（noVNC 首选 binary）
    # 若客户端未携带任何子协议，selected_protocol 置 None：
    # 按 RFC 6455，服务端不能在客户端未提供协议时在响应中返回协议，否则浏览器会立即关闭连接
    if "binary" in protocols:
        selected_protocol = "binary"
    elif "base64" in protocols:
        selected_protocol = "base64"
    else:
        logger.warning(f"{session_id} VNC Websocket端点连接未指定协议[{protocols_str}]，不协商子协议")
        selected_protocol = None

    try:
        # 先建立与沙箱 VNC 的连接，再 accept 客户端 WebSocket
        # 这样 noVNC accept 后可立即收到 RFB 握手数据，避免因延迟超时断开
        sandbox_vnc_url = await session_service.get_vnc_url(session_id)
        logger.info(f"获取到会话[{session_id}]的vnc连接url: {sandbox_vnc_url}")

        # 子协议与客户端协商结果保持一致
        vnc_subprotocols = [selected_protocol] if selected_protocol else []
        async with websockets.connect(sandbox_vnc_url, subprotocols=vnc_subprotocols) as sandbox_ws:
            # 沙箱 VNC 就绪后再向客户端完成 WebSocket 握手
            logger.info(f"{session_id} VNC Websocket端点连接已建立，使用协议: {selected_protocol}")
            await websocket.accept(subprotocol=selected_protocol)
            # 创建 2 个异步协程完成数据的双向转发
            async def forward_to_sandbox():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await sandbox_ws.send(data)
                except WebSocketDisconnect:
                    logger.info(f"{session_id} Web->VNC 数据转发中断")
                except Exception as forward_e:
                    logger.error(f"{session_id} Web->VNC 数据转发异常: {str(forward_e)}")

            async def forward_from_sandbox():
                try:
                    while True:
                        data = await sandbox_ws.recv()
                        await websocket.send_bytes(data)
                except ConnectionClosed:
                    logger.info(f"{session_id} VNC->Web 数据转发中断")
                except Exception as forward_e:
                    logger.error(f"{session_id} VNC->Web 数据转发异常: {str(forward_e)}")

            # 并行运行两个子恩物
            forward_task1 = asyncio.create_task(forward_to_sandbox())
            forward_task2 = asyncio.create_task(forward_from_sandbox())

            # 等待任意任何结束
            done, pending = await asyncio.wait(
                [forward_task1, forward_task2],
                return_when=asyncio.FIRST_COMPLETED,
            )
            logger.info(f"{session_id} VNC Websocket端点连接已关闭")

            # 取消未完成的任务
            for task in pending:
                task.cancel()
    except ConnectionError as connection_e:
        # 连接沙箱环境失败，关闭websocket
        logger.error(f"连接沙箱环境失败: {str(connection_e)}")
        await websocket.close(code=1011, reason=f"连接沙箱环境失败: {str(connection_e)}")
    except Exception as e:
        logger.error(f"VNC Websocket端点出现异常: {str(e)}")
        await websocket.close(code=1011, reason=f"VNC Websocket端点出现异常: {str(e)}")