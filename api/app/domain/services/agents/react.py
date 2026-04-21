
import logging
from typing import AsyncGenerator, List, Optional
from app.domain.models.event import BaseEvent, ErrorEvent, Event, MessageEvent, StepEvent, StepEventStatus, ThinkingEvent, TitleEvent, ToolEvent, ToolEventStatus, WaitEvent
from app.domain.models.file import File
from app.domain.models.message import Message
from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.services.prompts.react import EXECUTION_PROMPT, REACT_SYSTEM_PROMPT, SUMMARIZE_PROMPT
from app.domain.services.prompts.system import SYSTEM_PROMPT
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReActAgent(BaseAgent):
    """基于 ReAct 架构的执行 Agent"""
    name: str = "react"
    _system_prompt: str = SYSTEM_PROMPT + REACT_SYSTEM_PROMPT
    _format: str = "json_object" # format控制的是content、工具调用控制的是tool_calls两者不冲突

    async def execute_step(self, plan: Plan, step: Step, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """根据传递的消息+规划+子步骤，执行相应的子步骤"""
        # 1.根据传递的内容生成执行消息
        query = EXECUTION_PROMPT.format(
            message=message.message,
            attachments="\n".join(message.attachments),
            language=plan.language,
            step=step.description,
        )

        # 2.更新步骤的执行状态为运行中兵返回 Step 事件
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(step=step, status=StepEventStatus.STARTED)

        # 3.调用 invoke 获取 Agent 的返回内容
        async for event in self.invoke(query):
            # 4.判断事件类型执行不同操作
            if isinstance(event, ToolEvent):
                # 5.工具事件需要判断工具的名称是否为 message_ask_user
                if event.function_name == "message_ask_user":
                    # 6.工具如果在调用中，我们需要返回一条消息告知用户需要让用户处理什么
                    if event.status == ToolEventStatus.CALLING:
                        yield MessageEvent(
                            role="assistant",
                            message=event.function_args.get("text", "")
                        )
                    elif event.status == ToolEventStatus.CALLED:
                        # 7.如果工具事件为已调用，则需要返回等待事件并中断程序
                        yield WaitEvent()
                        return
                    continue
            elif isinstance(event, MessageEvent):
                # 8.返回消息事件，意味着 content有 内容，content 有内容则代表执行 Agent 已运行完毕
                step.status = ExecutionStatus.COMPLETED

                # 9.message 中输出的数据结构为 json，需要提取并解析
                parsed_obj = await self._json_parser.invoke(event.message)
                new_step = Step.model_validate(parsed_obj)

                # 10.更新子步骤的数据
                step.success = new_step.success
                step.result = new_step.result
                step.attachments = new_step.attachments

                # 11.返回步骤完成事件
                yield StepEvent(step=step, status=StepEventStatus.COMPLETED)

                # 12.如果子步骤拿到了结果，还需要返回一段消息给用户(将结果返回给用户)
                if step.result:
                    yield MessageEvent(role="assistant", message=step.result)
                continue
            elif isinstance(event, ErrorEvent):
                # 13. 错误事件更新步骤的状态
                step.status = ExecutionStatus.FAILED
                step.error = event.error

                # 14. 返回子步骤对应事件
                yield StepEvent(step=step, status=StepEventStatus.FAILED)
            
            # 15. 其他场景直接返回事件
            yield event
        
        # 16.循环迭代完成后代表子步骤已实现，需要更新状态
        step.status = ExecutionStatus.COMPLETED

    async def summarize(self) -> AsyncGenerator[BaseAgent, None]:
        """调用Agent汇总历史的消息并生成最终回复+附件"""
        # 1.构建请求 query
        query = SUMMARIZE_PROMPT

        # 2.直接调用流式LLM，传入空工具列表以强制启用 json_object response_format
        #   （若传工具列表，部分模型会禁用 response_format，导致 JSON 输出不稳定）
        await self._ensure_memory()
        message: Optional[dict] = None
        async for item in self._stream_invoke_llm(
            [{"role": "user", "content": query}],
            format=self._format,
            tools_override=[],
        ):
            if isinstance(item, ThinkingEvent):
                yield item
            else:
                message = item

        if message is None:
            yield ErrorEvent(error="LLM 汇总失败，未获取到有效响应")
            return

        # 3.记录日志并解析输出内容
        logger.info(f"执行Agent生成汇总内容: {message.get('content', '')}")
        parsed_obj = await self._json_parser.invoke(message.get("content", ""))

        # 4.将解析数据转换为Message对象
        summarize_message = Message.model_validate(parsed_obj)

        # 5.提取消息中的附件信息（LLM返回的文件路径列表）
        attachments: List[File] = [File(filepath=fp) for fp in summarize_message.attachments]

        # 6.如果 LLM 未提供附件，从 session 文件列表中获取作为兜底
        if not attachments:
            logger.info("LLM 汇总未提供附件，尝试从会话文件列表获取")
            try:
                async with self._uow:
                    session = await self._uow.session.get_by_id(self._session_id)
                if session and session.files:
                    attachments = list(session.files)
                    logger.info(f"从会话文件列表获取到 {len(attachments)} 个附件")
            except Exception as e:
                logger.warning(f"从会话文件列表获取附件失败: {str(e)}")

        # 7.返回消息事件并将消息+附件进行相应
        yield MessageEvent(
            role="assistant",
            message=summarize_message.message,
            attachments=attachments,
        )
