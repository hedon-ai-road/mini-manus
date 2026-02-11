import asyncio
import logging
from typing import Dict
import asyncio
from typing import Optional
import uuid

from app.domain.external.message_queue import MessageQueue
from app.domain.external.task import TaskRunner
from app.domain.external.task import Task
from app.infrastructure.external.message_queue.redis_message_queue import RedisStreamMessageQueue

logger = logging.getLogger(__name__)

class RedisStreamTask(Task):
    """基于 Redis Strean 的任务类"""

    _task_registry: Dict[str, "RedisStreamTask"] = {}

    def __init__(self, task_runner: TaskRunner) -> None:
        """构造函数，传递任务运行器，完成 Task 初始化"""
        self._task_runner = task_runner
        self._id = str(uuid.uuid4())
        self._execution_task: Optional[asyncio.Task] = None # 定义在后台执行的任务

        input_stream_name =f"task:input:{self._id}"
        output_stream_name = f"task:output:{self._id}"

        self._input_stream = RedisStreamMessageQueue(input_stream_name)
        self._output_stream = RedisStreamMessageQueue(output_stream_name)

        RedisStreamTask._task_registry[self._id] = self

    def _cleanup_registry(self) -> None:
        if self._id in RedisStreamTask._task_registry:
            del RedisStreamTask._task_registry[self._id]
            logger.info(f"任务[{self._id}]从注册中心移出")

    async def _on_task_done(self) -> None:
        """任务结束时的回调函数"""
        # 1. 执行回调函数
        if self._task_runner:
            asyncio.create_task(self._task_runner.on_done(self))

        # 2. 清除当前任务对应的资源
        self._cleanup_registry()

    async def _execute_task(self) -> None:
        """使用 TaskRunner 执行任务"""
        try:
            await self._task_runner.invoke(self)
        except asyncio.CancelledError as e:
            logger.info(f"任务[{self._id}]执行被取消")
        except Exception as e:
            logger.error(f"任务[{self.id}]执行出现异常: {str(e)}")
        finally:
            await self._on_task_done()

    async def invoke(self) -> None:
        """运行当前任务"""
        if not self.done():
            self._execution_task = asyncio.create_task(self._execution_task())
            logger.info(f"任务[{self._id}]开始执行")

    def cancel(self) -> bool:
        """取消当前任务"""
        if not self.done():
            self._execution_task.cancel()
            logger.info(f"任务[{self._id}]已取消")
        
        self._cleanup_registry()
        return True

    
    @property
    def input_stream(self) -> MessageQueue:
        """只读属性，返回任务的输入流"""
        return self._input_stream

    @property
    def output_stream(self) -> MessageQueue:
        """只读属性，返回任务的输出流"""
        return self._output_stream

    @property
    def id(self) -> str:
        """只读属性，返回任务的 ID"""
        return self._id
    
    @property
    def done(self) -> bool:
        """只读属性，返回任务是否结束"""
        if self._execution_task is None:
            return True
        return self._execution_task.done()

    @classmethod
    def get(cls, task_id: str) -> Optional["Task"]:
        """类方法，根据任务 id 获取对应任务"""
        return RedisStreamTask._task_registry.get(task_id)

    @classmethod
    def create(cls, task_runner: TaskRunner) -> "Task":
        """类方法，根据传递的任务运行器创建任务"""
        return cls(task_runner)
    
    @classmethod
    async def destory(cls) -> None:
        """销毁所有任务实例"""
        for task_id in RedisStreamTask._task_registry:
            task = RedisStreamTask._task_registry[task_id]
            task.cancel()

            if task._task_runner:
                await task._task_runner.destory()
        
        cls._task_registry.clear()
            