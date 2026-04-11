import logging
import time
from typing import AsyncGenerator, Optional

from app.domain.models.app_config import AgentConfig
from app.domain.models.event import BaseEvent, DoneEvent, MessageEvent, PlanEvent, PlanEventStatus, TitleEvent
from app.domain.models.plan import ExecutionStatus, Plan
from app.domain.models.session import SessionStatus
from app.domain.services.flows.base import BaseFlow, FlowStatus
from app.domain.external.llm import LLM
from app.domain.models.message import Message
from app.domain.repositories.session_repository import SessionRepository
from app.domain.external.json_parser import JsonParser
from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.a2a import A2ATool
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.mcp import MCPTool
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.browser import BrowserTool
from app.domain.services.tools.search import SearchTool
from app.domain.services.tools.message import MessageTool
from app.domain.external.search import SearchEngine
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.agents.react import ReActAgent

logger = logging.getLogger(__name__)

class PlannerReActFlow(BaseFlow):
    """规划+执行流"""

    def __init__(
        self,
        session_id: str, # 会话 ID
        session_repository: SessionRepository, # 会话仓库
        llm: LLM, # 语言模型
        agent_config: AgentConfig, # Agent 配置
        json_parser: JsonParser, # JSON 输出解析器
        browser: Browser, # 浏览器
        sandbox: Sandbox, # 沙箱
        search_engine: SearchEngine, # 搜索引擎
        mcp_tool: MCPTool, # MCP 工具
        a2a_tool: A2ATool, # A2A 工具
    ) -> None:
        # 初始化配置数据
        self._session_id = session_id
        self._session_repository = session_repository
        self.status = FlowStatus.IDLE
        self.plan: Optional[Plan] = None

        # 初始化 Agent 预设工具
        tools = [
            FileTool(sandbox=sandbox),
            ShellTool(sandbox=sandbox),
            BrowserTool(browser=browser),
            SearchTool(search_engine=search_engine),
            MessageTool(),
            mcp_tool,
            a2a_tool,
        ]

        # 创建规划 Agent
        self.planner = PlannerAgent(
            session_id=session_id,
            session_repository=session_repository,
            agent_config=agent_config,
            llm=llm,
            json_parser=json_parser,
            tools=tools,
        )
        logger.debug(f"规划 Agent 创建成功，会话ID: {session_id}")

        # 创建执行 Agent
        self.react = ReActAgent(
            session_id=session_id,
            session_repository=session_repository,
            agent_config=agent_config,
            llm=llm,
            json_parser=json_parser,
            tools=tools,
        )
        logger.debug(f"执行 Agent 创建成功，会话ID: {session_id}")

    async def invoke(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """流调用函数，返回可迭代的基础事件"""
        # 判断会话是否存在
        session = await self._session_repository.get_by_id(self._session_id)
        if not session:
            raise ValueError(f"会话 {self._session_id} 不存在，请核实后重试！")

        # 判断会话的状态是不是 PENDING，如果不是则可能有两种状态
        # - 任务未完成，还在运行，但是用户又传递一条消息
        # - Agent 在等待人类输入，这时候人类输入了
        # 这个时候均需要处理历史消息列表，避免 AI（工具调用消息）后直接接上人类消息
        if session.status != SessionStatus.PENDING:
            logger.debug(f"会话[{self._session_id}] 未处于 PENDING 状态，回滚数据确保消息列表格式正确")
            await self.planner.roll_back(message)
            await self.react.roll_back(message)
        
        # 如果会话状态等于 RUNNING，则流需要重新规划内容
        if session.status == SessionStatus.RUNNING:
            logger.debug(f"会话[{self._session_id}] 处于 RUNNING 状态，重新规划内容")
            self.status = FlowStatus.PLANNING
        
        # 如果会话状态等于 WAITING，则需要修改流状态为执行中
        if session.status == SessionStatus.WAITING:
            logger.debug(f"会话[{self._session_id}] 处于 WAITING 状态，修改流状态为执行中")
            self.status = FlowStatus.EXECUTING
        
        # 更新会话状态为 RUNNING
        await self._session_repository.update_status(self._session_id, SessionStatus.RUNNING)

        # 获取当前会话中最新事件
        self.plan = session.get_latest_plan()

        # 定义当前正在执行的子步骤
        step = None

        # 循环取出规划中的子步骤，让执行 Agent 执行，依次迭代
        while True:
            if self.status == FlowStatus.IDLE:
                logger.info(f"Planner&ReAct流状态从{FlowStatus.IDLE}变成{FlowStatus.PLANNING}")
                self.status = FlowStatus.PLANNING
            elif self.status == FlowStatus.PLANNING:
                logger.info(f"Planner&ReAct流开始创建计划/Plan")
                async for event in self.planner.create_plan(message):
                    # 判断 Planner 是否返回规划事件
                    if isinstance(event, PlanEvent) and event.status == PlanEventStatus.CREATED:
                        # 创建计划成功时需要更新计划
                        self.plan = event.plan
                        logger.info(f"Planner&ReAct流成功创建计划，共计: {len(event.plan.steps)} 步")

                        # 在计划中同步生成了会话标题+初始AI消息
                        yield TitleEvent(title=event.plan.title)
                        yield MessageEvent(role="assistant", message=event.plan.message)
                    
                    # 将生成的事件直接输出（一般来说是 PlanEvent）
                    yield event
                
                # 事件创建成功，更新流状态为执行中
                logger.info(f"Planner&ReAct流状态从{FlowStatus.PLANNING}变成{FlowStatus.EXECUTING}")
                self.status = FlowStatus.EXECUTING

                # 判断计划是否完成，步骤是否正常
                if not self.plan or len(self.plan.steps) == 0:
                    logger.info(f"Planner&ReAct流计划为空，可能创建失败，流状态从{FlowStatus.EXECUTING}变成{FlowStatus.COMPLETED}")
                    self.status = FlowStatus.COMPLETED
            elif self.status == FlowStatus.EXECUTING:
                # 流的状态为执行中，先将计划状态调整为运行中，同时调用执行 Agent 完成每个子步骤
                self.plan.status = ExecutionStatus.RUNNING

                # 获取当前计划的下一个需要执行的子步骤
                step = self.plan.get_next_step()

                # 如果不存在下一个需要执行的子步骤，则更新流状态为执行后续步骤
                if not step:
                    logger.info(f"Planner&ReAct流没有需要执行的子步骤，流状态从{FlowStatus.EXECUTING}变成{FlowStatus.SUMMARIZING}")
                    self.status = FlowStatus.SUMMARIZING
                    continue

                # 执行 ReAct Agent 执行对应步骤
                logger.info(f"Planner&ReAct流开始执行子步骤 {step.id}: {step.description[:50]}...")
                async for event in self.react.execute_step(self.plan, step, message):
                    yield event
                
                # 压缩执行 Agent 记忆，避免上下文腐化+消耗大量 token
                logger.info(f"Planner&ReAct流开始压缩执行 Agent [{self.react.name}] 记忆")
                await self.react.compact_memory()

                # 将状态更新wield UPDATING
                self.status = FlowStatus.UPDATING
            elif self.status == FlowStatus.UPDATING:
                # 流的状态为更新中，调用 Planner Agent 更新计划
                logger.info(f"Planner&ReAct流开始更新计划")
                async for event in self.planner.update_plan(self.plan, step):
                    yield event
                
                # 计划更新完毕，需要执行相应的子步骤
                logger.info(f"Planner&ReAct流状态从{FlowStatus.UPDATING}变成{FlowStatus.EXECUTING}")
                self.status = FlowStatus.EXECUTING
            elif self.status == FlowStatus.SUMMARIZING:
                # 流状态为总结中，则意味着所有子步骤都执行完毕
                logger.info(f"Planner&ReAct流开始总结所有子步骤")
                async for event in self.react.summarize():
                    yield event
                
                # 总结完毕，更新流状态为完成
                logger.info(f"Planner&ReAct流状态从{FlowStatus.SUMMARIZING}变成{FlowStatus.COMPLETED}")
                self.status = FlowStatus.COMPLETED
            elif self.status == FlowStatus.COMPLETED:
                # 流状态为完成，则意味着所有子步骤都执行完毕，更新plan状态，并发送计划事件通知API已完成
                self.plan.status = ExecutionStatus.COMPLETED
                self.status = FlowStatus.IDLE
                yield PlanEvent(plan=self.plan, status=PlanEventStatus.COMPLETED)
                break
            else:
                raise Exception(f"Planner&ReAct流状态[{self.status}] 不合法，请检查代码！")
        
        # 任务完成
        yield DoneEvent()
        logger.info(f"Planner&ReAct流任务完成，会话ID: {self._session_id}")

    
    @property
    def done(self) -> bool:
        """流是否结束"""
        return self.status == FlowStatus.IDLE