from _typeshed import Self
from typing import BinaryIO, Optional, Protocol

from app.domain.external.browser import Browser
from app.domain.models.tool_result import ToolResult


class Sandbox(Protocol):
    """沙箱服务扩展协议，包含文件工具协议、Shell 工具协议以及沙箱本身的扩展"""

    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        """根据传递的会话ID+目录+命令执行对应的命令"""
        ...
    
    async def read_shell_output(self, session_id: str, console: bool = False) -> ToolResult:
        """根据传递的会话ID+是否返回控制台记录获取 shell 结果"""
        ...

    async def wait_process(self, session_id: str, seconds: Optional[int] = None) -> ToolResult:
        """根据传递的会话ID+秒数等待程序执行"""
        ...

    async def write_shell_input(
        self,
        session_id: str,
        input_text: str,
        press_enter: bool = True,
    ) -> ToolResult:
        """根据传递会话ID+文本内容+是否回车键写入内容到进程中"""
        ...

    async def kill_process(self, session_id: str) -> ToolResult:
        """杀死某个进程"""
        ...

    async def file_write(
        self,
        filepath: str,
        content: str,
        append: bool = False,
        leading_new_line: bool = False,
        trailing_new_line: bool = False,
        sudo: bool = False
    ) -> ToolResult:
        """写入文件"""
        ...
    
    async def file_read(
        self,
        filepath: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        sudo: bool = False,
    ) -> ToolResult:
        """读取文件"""
        ...

    async def file_exists(self, filepath: str) -> ToolResult:
        """判断文件是否存在"""
        ...

    async def file_delete(self, filepath: str) -> ToolResult:
        """删除文件"""
        ...
    
    async def file_list(self, dir_path: str) -> ToolResult:
        """列出目录的文件列表"""
        ...
    
    async def file_replace(
        self,
        filepath: str,
        old_str: str,
        new_str: str,
        sudo: bool = False,
    ) -> ToolResult:
        """文件内容替换"""
        ...

    async def file_search(self, filepath: str, regex: str, sudo: bool = False) -> ToolResult:
        """文件内容搜索"""
        ...

    async def file_find(self, dir_path: str, glob_pattern: str) -> ToolResult:
        """查询文件"""
        ...

    async def file_upload(
        self,
        file_data: BinaryIO,
        filepath: str,
        filename: str = None,
    ) -> ToolResult:
        """上传文件"""
        ...

    async def file_download(self, filepath: str) -> ToolResult:
        """文件下载"""
        ...

    async def ensure_sandbox(self) -> None:
        """确保沙箱存在，不存在则创建"""
        ...

    async def destory(self) -> bool:
        """销毁当前沙箱，成功则返回True"""
        ...

    async def get_browser(self) -> Browser:
        """获取沙箱中的浏览器实例"""
        ...

    @property
    def id(self) -> str:
        """沙箱ID"""
        ...
    
    @property
    def cdp_url(self) -> str:
        """沙箱CDP链接"""
        ...
    
    @property
    def vnc_url(self) -> str:
        """获取沙箱的VNC链接，用于远程桌面链接"""
        ...

    @classmethod
    async def create(cls) -> Self:
        """创建一个沙箱"""
        ...

    @classmethod
    async def get(cls, id: str) -> Self:
        """获取沙箱实例"""
        ...
