from _typeshed import Self
import logging
from docker.models.resource import Model
import httpx
import asyncio
import socket
import uuid
import docker
from docker.errors import NotFound as DockerNotFoundError
from typing import Optional
from async_lru import alru_cache

from app.domain.external.browser import Browser
from app.domain.external.sandbox import Sandbox
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