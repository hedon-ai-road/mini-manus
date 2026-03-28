import http
import logging
import socket
import asyncio
from typing import Any, List
from xmlrpc import client as xmlrpcclient
from http import client as httpclient

from app.core.config import get_settings
from app.interfaces.errors.exception import AppException, BadRequestException
from app.models.supervisor import ProcessInfo

"""
1.Supervisor启动后，通过一个Unix套接字文件来实现通信(rpc协议)
2.连接这个通信文件，/tmp/supervisor.sock (xml-rpc连接)
3.使用某种方式来完整转换，让xml-rpc实现连接supervisor.sock
4.连接之后我们就可以调用rpc对应的方法，getAllProcessInfo()
"""

logger = logging.getLogger(__name__)

class UnixStreamHTTPConnection(httpclient.HTTPConnection):
    """基于Unix流的HTTP连接处理器"""
    def __init__(self, host: str, socket_path: str, timeout=None) -> None:
        """构造函数，完成连接处理器初始化"""
        httpclient.HTTPConnection.__init__(self, host, timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        """重写连接方法，欺骗xml-rpc库让其觉得自己正在进行网络连接"""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

class UnixStreamTransport(xmlrpcclient.Transport):
    """基于Unix流传输层的适配器/转换器"""
    def __init__(self, socket_path: str) -> None:
        xmlrpcclient.Transport.__init__(self)
        self.socket_path = socket_path

    def make_connection(self, host) -> http.client.HTTPConnection:
        return UnixStreamHTTPConnection(host, self.socket_path)

class SupervisorService:
    """Supervisor服务"""
    def __init__(self) -> None:
        """构造函数，完成supervisor服务链接"""

        # 1. 连接 supervisor 配置
        self.rpc_url = "/tmp/supervisor.sock"
        self._connect_rpc()

        # 2. supervisor 超时配置
        settings = get_settings()

    def _connect_rpc(self) -> None:
        """使用python的xml-rpc连接一个本地socket文件实现连接rpc服务"""
        try:
            self.server: xmlrpcclient.ServerProxy = xmlrpcclient.ServerProxy(
                "http://localhost",
                transport=UnixStreamTransport(self.rpc_url)
            )
        except Exception as e:
            logger.error(f"连接 supervisor 服务失败: {str(e)}")
            raise BadRequestException(f"连接 supervisor 服务失败: {str(e)}")

    @classmethod
    async def _call_rpc(cls, method, *args) -> Any:
        """根据传递的方法+参数调用rpc方法"""
        try:
            return await asyncio.to_thread(method, *args)
        except Exception as e:
            logger.error(f"RPC方法调用失败: {str(e)}")
            raise BadRequestException(f"RPC方法调用失败: {str(e)}")

    async def get_all_processes(self) -> List[ProcessInfo]:
        """获取当前 supervisor 管理的所有进程信息"""
        try:
            processes = await self._call_rpc(self.server.supervisor.getAllProcessInfo)
            return [ProcessInfo(**process) for process in processes]
        except Exception as e:
            logger.error(f"获取进程信息失败: {str(e)}")
            raise AppException(f"获取进程信息失败: {str(e)}")