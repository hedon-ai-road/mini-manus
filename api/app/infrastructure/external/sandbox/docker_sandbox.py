import logging
from docker.models.resource import Model
import httpx
import asyncio
import socket
import uuid
import docker
import io
from _typeshed import Self
from docker.errors import NotFound as DockerNotFoundError
from typing import BinaryIO, Optional
from async_lru import alru_cache

from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult
from app.application.errors.exceptions import AppException
from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser
from core.config import get_settings

logger = logging.getLogger(__name__)

class DockerSandbox(Sandbox):
    def __init__(
        self,
        ip: Optional[str] = None,
        container_name: Optional[str] = None
    ) -> None:
        """构造函数，完成 Docker 沙箱扩展构建"""
        self.client = httpx.AsyncClient(timeout=600)
        self._ip = ip
        self._container_name = container_name
        self._base_url = f"http://{ip}:9528"
        self._vnc_url = f"ws://{ip}:5901"
        self._cdp_url = f"http://{ip}:9222"

    @property
    def id(self) -> str:
        """获取沙箱的唯一 ID"""
        if not self._container_name:
            return "minu-manus-sandbox"
        return self._container_name
    
    @property
    def vnc_url(self) -> str:
        return self._vnc_url
    
    @property
    def cdp_url(self) -> str:
        return self._cdp_url

    @classmethod
    def _get_container_ip(cls, container: Model) -> str | None:
        """获取容器 IP 地址"""
        # 获取 inspect 网络设置
        network_settings = container.attrs["NetworkSettings"]
        ip_address = network_settings["IPAddress"]

        # 判断容器是否存在 ip，如果不存在则从 networks 中获取
        if not ip_address and "Networks" in network_settings:
            networks = network_settings["Networks"]
            for network_name, network_config in networks.items():
                if "IPAddress" in network_config and network_config["IPAddress"]:
                    ip_address = network_config["IPAddress"]
                    break

        return ip_address

    
    @classmethod
    @alru_cache(maxsize=128, typed=True)
    async def _resolve_hostname_to_ip(cls, hostname: str) -> str | None:
        """将主机名解析成 IP 地址"""
        try:
            # 解析传递的 hostname 是不是 IP
            try:
                socket.inet_aton(socket.AF_INET, hostname)
                return hostname
            except OSError:
                pass

            # 使用 socket 获取地址信息
            addr_info = socket.getaddrinfo(hostname,None, family=socket.AF_INET)
            if addr_info and len(addr_info) > 0:
                return addr_info[0][4][0]
            
            return None
        except Exception as e:
            logger.error(f"解析 Docker 容器主机名[{hostname}]失败: {str(e)}")
            raise

    @classmethod
    def _create_task(cls) -> Self:
        """创建沙箱容器的异步任务"""
        settings = get_settings()

        # 构建容器名字
        image_name = settings.sandbox_image
        name_prefix = settings.sandbox_name_prefix
        container_name = f"{name_prefix}-{str(uuid.uuid4())[:8]}"

        try:
            # 创建 Docker 客户端
            
            client = docker.from_env()

            # 创建 Docker 容器
            container: Model = client.containers.run(
                image=image_name,
                name=container_name,
                network=settings.sandbox_network if settings.sandbox_network else None,
                detach=True, # 后台运行
                remove=True, # 容器退出后删除
                environment={
                    "SERVICE_TIMEOUT_MINUTES": settings.sandbox_ttl_minutes,
                    "CHROME_ARGS": settings.sandbox_chrome_args,
                    "HTTPS_PROXY": settings.sandbox_https_proxy,
                    "HTTP_PROXY": settings.sandbox_http_proxy,
                    "NO_PROXY": settings.sandbox_no_proxy,
                },
            )

            # 重载并刷新容器信息
            container.reload()

            # 返回沙箱对象
            return cls(
                ip=cls._get_container_ip(container),
                container_name=container_name,
            )
        except Exception as e:
            logger.error(f"创建 Docker 沙箱容器[{container_name}]失败: {str(e)}")
            raise

        
    @classmethod
    async def create(cls) -> Self:
        """创建沙箱容器"""
        settings = get_settings()

        # 判断是否使用现场的沙箱
        if settings.sandbox_address:
            # 将沙箱主机地址解析成 IP
            ip = await cls._resolve_hostname_to_ip(settings.sandbox_address)
            return DockerSandbox(ip=ip)
        
        # 使用子线程创建一个容器后返回
        return await asyncio.to_thread(cls._create_task)

    async def destroy(self) -> bool:
        """销毁当前的 Docker Sandbox 实例"""
        try:
            # 关闭 HTTP 客户端
            if self.client:
                await self.client.aclose()
                self.client = None

            # 关闭并移除容器
            if self._container_name:
                client = docker.from_env()
                container: Model = client.containers.get(self._container_name)
                container.remove(force=True)
            return True
        except DockerNotFoundError:
            logger.warning(f"Docker 沙箱容器[{self._container_name}]不存在，跳过销毁")
            return True
        except Exception as e:
            logger.error(f"销毁 Docker 沙箱容器[{self._container_name}]失败: {str(e)}")
            return False
        finally:
            # 清除缓存
            DockerSandbox._resolve_hostname_to_ip.cache_clear()

    @classmethod
    @alru_cache(maxsize=128, typed=True)
    async def get(cls, id: str) -> Self | None:
        """根据传递的 id 获取对应的 Docker Sandbox 实例"""

        # 直连沙箱直接获取 IP
        settings = get_settings()
        if settings.sandbox_address:
            ip = await cls._resolve_hostname_to_ip(settings.sandbox_address)
            return DockerSandbox(ip=ip, container_name=id)
        
        # 创建 docker 客户端并根据容器名字获取容器
        try:
            client = docker.from_env()
            container: Model = client.containers.get(id)
            container.reload()
            return cls(
                ip=cls._get_container_ip(container),
                container_name=id,
            )
        except DockerNotFoundError:
            logger.warning(f"Docker 沙箱容器[{id}]不存在，返回 None")
            return None
        except Exception as e:
            logger.error(f"获取 Docker 沙箱容器[{id}]失败: {str(e)}")
            return None

    async def get_browser(self) -> Browser:
        """获取当前沙箱的浏览器实例"""
        return PlaywrightBrowser(cdp_url=self.cdp_url)

    async def ensure_sandbox(self) -> None:
        """确保沙箱存在/服务全部都开启了才执行后续步骤"""
        max_retries = 30 # 最大重试次数
        retry_interval = 2 # 重试间隔时间(2s)
        
        # 循环请求 supervisor 状态并判断服务是否正常
        for attempt in range(max_retries):
            try:
                # 请求 supervisor 状态
                response: httpx.Response = await self.client.get(f"{self._base_url}/api/supervisor/status")
                response.raise_for_status()
                tool_result = ToolResult.from_sandbox(**response.json())
                if not tool_result.success:
                    logger.warning(f"supervisor 服务未正常运行: {tool_result.message}")
                    await asyncio.sleep(retry_interval)
                    continue

                # 获取 supervisor 进程中所有服务
                services = tool_result.data or []
                if not services:
                    logger.warning("supervisor 进程中未发现任何服务")
                    await asyncio.sleep(retry_interval)
                    continue

                # 判断服务是否全部开启
                all_running = True
                not_running_services = []
                for service in services:
                    service_name = service.get("name", "unknown")
                    state_name = service.get("statename", "")
                    if state_name != "RUNNING":
                        all_running = False
                        not_running_services.append(f"{service_name}({state_name})")

                if not all_running:
                    logger.info(f"supervisor 进程中以下服务未正常运行: {', '.join(not_running_services)}")
                    await asyncio.sleep(retry_interval)
                    continue

                logger.info("supervisor 进程中所有服务均正常运行")
                return
            except Exception as e:
                logger.error(f"请求 supervisor 状态失败: {str(e)}")
                await asyncio.sleep(retry_interval)

        logger.error(f"经过 {max_retries} 次重试，supervisor 服务仍未正常运行")
        raise Exception(f"经过 {max_retries} 次重试，supervisor 服务仍未正常运行")

    async def read_file(
            self,
            filepath: str,
            start_line: Optional[int] = None,
            end_line: Optional[int] = None,
            sudo: bool = False,
            max_length: int = 10000
    ) -> ToolResult:
        """读取沙箱中指定路径的文件内容"""
        response = await self.client.post(
            f"{self._base_url}/api/file/read-file",
            json={
                "filepath": filepath,
                "start_line": start_line,
                "end_line": end_line,
                "sudo": sudo,
                "max_length": max_length,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def write_file(
            self,
            filepath: str,
            content: str,
            append: bool = False,
            leading_newline: bool = False,
            trailing_newline: bool = False,
            sudo: bool = False,
    ) -> ToolResult:
        """向沙箱中指定文件写入内容"""
        response = await self.client.post(
            f"{self._base_url}/api/file/write-file",
            json={
                "filepath": filepath,
                "content": content,
                "append": append,
                "leading_newline": leading_newline,
                "trailing_newline": trailing_newline,
                "sudo": sudo,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def replace_in_file(
            self,
            filepath: str,
            old_str: str,
            new_str: str,
            sudo: bool = False,
    ) -> ToolResult:
        """替换沙箱中文件的旧内容为指定内容"""
        response = await self.client.post(
            f"{self._base_url}/api/file/replace-in-file",
            json={
                "filepath": filepath,
                "old_str": old_str,
                "new_str": new_str,
                "sudo": sudo,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def search_in_file(self, filepath: str, regex: str, sudo: bool = False) -> ToolResult:
        """搜索沙箱中指定文件的内容"""
        response = await self.client.post(
            f"{self._base_url}/api/file/search-in-file",
            json={
                "filepath": filepath,
                "regex": regex,
                "sudo": sudo,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def find_files(self, dir_path: str, glob_pattern: str) -> ToolResult:
        """查找沙箱中指定目录的文件列表"""
        response = await self.client.post(
            f"{self._base_url}/api/file/find-files",
            json={
                "dir_path": dir_path,
                "glob_pattern": glob_pattern,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def list_files(self, dir_path: str) -> ToolResult:
        """传递目录列出沙箱指定目录下的所有文件"""
        return await self.find_files(dir_path, "*")

    async def check_file_exists(self, filepath: str) -> ToolResult:
        """传递指定路径检查沙箱中指定文件是否存在"""
        response = await self.client.post(
            f"{self._base_url}/api/file/check-file-exists",
            json={
                "filepath": filepath,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def delete_file(self, filepath: str) -> ToolResult:
        """传递路径删除指定的文件"""
        response = await self.client.post(
            f"{self._base_url}/api/file/delete-file",
            json={
                "filepath": filepath,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def upload_file(
            self,
            file_data: BinaryIO,
            filepath: str,
            filename: str = None,
    ) -> ToolResult:
        """将文件源上传至沙箱指定位置"""
        # 1.预配置上传数据
        files = {"file": (filename or "upload", file_data, "application/octet-stream")}
        data = {"filepath": filepath}

        # 2.发起请求上传数据获取响应
        response = await self.client.post(
            f"{self._base_url}/api/file/upload-file",
            files=files,
            data=data,
        )
        return ToolResult.from_sandbox(**response.json())

    async def download_file(self, filepath: str) -> BinaryIO:
        """从沙箱中下载文件"""
        response = await self.client.get(
            f"{self._base_url}/api/file/download-file",
            params={"filepath": filepath}
        )
        response.raise_for_status()

        return io.BytesIO(response.content)

    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        """在沙箱中执行命令"""
        response = await self.client.post(
            f"{self._base_url}/api/shell/exec-command",
            json={
                "session_id": session_id,
                "exec_dir": exec_dir,
                "command": command,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def read_shell_output(self, session_id: str, console: bool = False) -> ToolResult:
        """读取沙箱中shell的输出"""
        response = await self.client.post(
            f"{self._base_url}/api/shell/read-shell-output",
            json={
                "session_id": session_id,
                "console": console,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def write_shell_input(
            self,
            session_id: str,
            input_text: str,
            press_enter: bool = True,
    ) -> ToolResult:
        """向沙箱的Shell进程写入数据"""
        response = await self.client.post(
            f"{self._base_url}/api/shell/write-shell-input",
            json={
                "session_id": session_id,
                "input_text": input_text,
                "press_enter": press_enter,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def wait_process(self, session_id: str, seconds: Optional[int] = None) -> ToolResult:
        """等待沙箱中进程的执行"""
        response = await self.client.post(
            f"{self._base_url}/api/shell/wait-process",
            json={
                "session_id": session_id,
                "seconds": seconds,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    async def kill_process(self, session_id: str) -> ToolResult:
        """杀死沙箱中指定进程"""
        response = await self.client.post(
            f"{self._base_url}/api/shell/kill-process",
            json={
                "session_id": session_id,
            }
        )
        return ToolResult.from_sandbox(**response.json())

    