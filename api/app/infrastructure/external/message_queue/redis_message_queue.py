from sqlalchemy import false
import asyncio
import uuid
from typing import Optional
import logging
from typing import Any, Tuple
from app.domain.external.message_queue import MessageQueue
from app.infrastructure.storage.redis import get_redis

logger = logging.getLogger(__name__)

class RedisStreamMessageQueue(MessageQueue):
    """基于 Redis Stream 的消息队列"""

    def __init__(self, stream_name: str) -> None:
        self._stream_name = stream_name
        self._redis = get_redis()
        self._lock_expire_seconds = 10

    async def _acquire_lock(self, lock_key: str, timeout_seconds: int = 5) -> Optional[str]:
        lock_value = str(uuid.uuid4())
        end_time = timeout_seconds

        while end_time > 0:
            result = await self._redis.client.set(
                lock_key,
                lock_value,
                nx=True,
                ex=timeout_seconds,
            )
            if result:
                return lock_value
            
            await asyncio.sleep(0.1)
            end_time -= 0.1
        
        return None
    
    async def _release_lock(self, lock_key: str, lock_value: str) -> bool:
        release_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DELETE", KEYS[1])
        else
            return 0
        end
        """
        try:
            script = self._redis.client.register_script(release_script)
            result = await script(keys=[lock_key], args=[lock_value])
            return result == 1
        except Exception as e:
            logger.error(f"释放锁[{lock_key}:{lock_value}]失败: {str(e)}")
            return False
    
    async def put(self, message: Any) -> str:
        """往消息队列中添加一条消息"""
        logger.debug(f"往消息队列[{self._stream_name}]中添加一条消息: {message}")
        return await self._redis.client.xadd(self._stream_name, {"data": message})

    async def get(self, start_id: str = None, block_ms: int = None) -> Tuple[str, Any]:
        """根据传递的开始 id + 阻塞实践，获取 1 条数据"""
        logger.debug(f"从消息队列[{self._stream_name}]中获取一条消息")
        if start_id is None:
            start_id = '0'
        
        messages = await self._redis.client.xrange(
            {self._stream_name: start_id},
            count=1,
            block=block_ms,
        )
        if not messages:
            return None, None
        
        stream_messages = messages[0][1]
        if not stream_messages:
            return None, None
        
        message_id, message_data = stream_messages[0]
        try:
            return message_id, message_data.get("data")
        except Exception as e:
            logger.error(f"从消息队列[{self._stream_name}]获取数据失败: {str(e)}")
    
    async def pop(self) -> Tuple[str, Any]:
        """获取并移出消息队列中的第一条消息"""
        logger.debug(f"从消息队列[{self._stream_name}]中弹出第一条消息")
        lock_key = f"lock:{self._stream_name}:pop"

        lock_value = await self._acquire_lock(lock_key)
        if not lock_value:
            return None
        
        try:
            messages = await self._redis.client.xrange(self._stream_name, "-", "+", count=1)
            if not messages:
                return None, None
            
            message_id, message_data = messages[0]
            await self._redis.client.xdel(self._stream_name, message_id)
            return message_id, message_data.get("data")
        except Exception as e:
            logger.error(f"解析消息队列[{self._stream_name}]出错: {str(e)}")
        finally:
            await self._release_lock(lock_key, lock_value)

    async def clear(self) -> None:
        """清空消息队列"""
        await self._redis.client.xtrim(self._stream_name, maxlen=0)
    
    async def is_empty(self) -> bool:
        """判断消息队列是否为空"""
        return await self.size() == 0

    async def size(self) -> int:
        """获取消息队列的长度"""
        return await self._redis.client.xlen(self._stream_name)

    async def delete_message(self, message_id: str) -> bool:
        """根据传递的消息 id 删除对应的消息"""
        try:
            await self._redis.client.xdel(self._stream_name, message_id)
            return True
        except Exception as e:
            logger.error(f"删除消息 {message_id} 出错: {str(e)}")
            return false