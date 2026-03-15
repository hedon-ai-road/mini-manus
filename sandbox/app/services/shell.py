import asyncio
import os
import re
import sys
from typing import Dict, List, Optional
import uuid
import logging
import getpass
import socket
import shutil
import codecs
import locale

from app.models.shell import ConsoleRecord, Shell, ShellExecResult, ShellKillResult, ShellViewResult, ShellWaitResult, ShellWriteResult
from app.interfaces.errors.exception import AppException, BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

class ShellService:
    """shell 命令服务"""

    active_shells: Dict[str, Shell] = {}

    @classmethod
    def _get_display_path(cls, path: str) -> str:
        """获取显示路径，将用户主目录替换成~"""
        home_dir = os.path.expanduser("~")
        logger.debug(f"主目录: {home_dir}，路径: {path}")
        if path.startswith(home_dir):
            return path.replace(home_dir, "~", 1)
        return path

    def _format_ps1(self, exec_dir: str) -> str:
        """格式化命令结构提示，增强交互体验，例如: root@myserver:/var/log $"""
        username = getpass.getuser()
        hostname = socket.gethostname()
        display_dir = self._get_display_path(exec_dir)
        return f"{username}@{hostname}:{display_dir}"

    @classmethod
    async def _create_process(cls, exec_dir: str, command: str) -> asyncio.subprocess.Process:
        """根据传递的执行目录+命令创建一个 asyncio 管理的子进程"""
        logger.debug(f"在目录 {exec_dir} 下使用命令 {command} 创建一个子进程")
        shell_exec = None
        if sys.platform != "win32":
            if os.path.exists("/bin/bash"):
                shell_exec = "/bin/bash"
            elif os.path.exists("/bin/zsh"):
                shell_exec = "/bin/zsh"
        elif sys.platform == "win32":
            shell_exec = shutil.which("powershell")
            if not shell_exec:
                shell_exec = shutil.which("cmd")
        
        return await asyncio.create_subprocess_shell(
            cmd=command,
            executable=shell_exec,
            cwd=exec_dir,
            stdout=asyncio.subprocess.PIPE, # 创建管道以捕获标准输出
            stderr=asyncio.subprocess.STDOUT, # 将标准错误重定向到标准输出流
            stdin=asyncio.subprocess.PIPE, # 创建管道以允许标准输入
            limit=1024*1024, # 缓冲区限制 1MB
        )

    async def _start_output_reader(self, session_id: str, process: asyncio.subprocess.Process) -> None:
        """启动协程以连续读取进程输出并将其存储到会话中"""
        logger.debug(f"正在弃用会话输出读取器: {session_id}")
        if sys.platform == "win32":
            encoding = "gb18030"
        else:
            encoding = "utf-8"
        decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
        shell = self.active_shells.get(session_id)

        while True:
            # 判断子进程是否有标准输出管道
            if process.stdout:
                try:
                    # 读取缓冲区
                    buffer = await process.stdout.read(4096)
                    if not buffer:
                        break
                    output = decoder.decode(buffer, final=False)

                    if shell:
                        shell.output += output
                        if shell.console_records:
                            shell.console_records[-1].output += output
                except Exception as e:
                    logger.error(f"读取进程输出时出现错误: {str(e)}")
                    break
            else:
                break

        logger.debug(f"会话 {session_id} 的输出读取器已完成")

    @classmethod
    def _remove_ansi_escape_codes(cls, text: str) -> str:
        """从文本中删除ANSI转义字符"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub("", text)

    @classmethod
    def create_session_id(cls) -> str:
        """创建会话id"""
        session_id = str(uuid.uuid4())
        logger.info(f"创建一个新的会话: {session_id}")
        return session_id

    def get_console_records(self, session_id: str) -> List[ConsoleRecord]:
        """从指定会话中获取控制台记录"""
        logger.debug(f"正在获取Shell会话的控制台记录: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"Shell会话不存在: {session_id}")
            raise NotFoundException(f"Shell会话不存在: {session_id}")
        
        console_records = self.active_shells[session_id].console_records
        clean_console_records = []

        for console_record in console_records:
            clean_console_records.append(ConsoleRecord(
                ps1=console_record.ps1,
                command=console_record.command,
                output=self._remove_ansi_escape_codes(console_record.output),
            ))
        return clean_console_records

    async def wait_for_process(self, session_id: str, seconds: Optional[int] = None) -> ShellWaitResult:
        """等待子进程结束，结果代码"""
        logger.debug(f"正在 shell 会话中等待进程: {session_id}, 超时时间: {seconds}s")
        if session_id not in self.active_shells:
            logger.error(f"shell 会话不存在: {session_id}")
            raise NotFoundException(f"shell 会话不存在: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell.process

        try:
            seconds = 60 if seconds is None or seconds <= 0 else seconds
            await asyncio.wait_for(process.wait(), timeout=seconds)

            logger.info(f"进程已完成，返回代码为: {process.returncode}")
            return ShellWaitResult(returncode=process.returncode)
        except asyncio.TimeoutError:
            logger.warning(f"shell 会话进程等待超时: {seconds}s")
            raise BadRequestException(f"shell 会话进程等待超时: {seconds}s")
        except Exception as e:
            logging.error(f"shell 会话进程等待异常: {str(e)}")
            raise AppException(f"shell 会话进程等待异常: {str(e)}")

    async def view_shell(self, session_id: str, console: bool = False) -> ShellViewResult:
        """获取 shell 命令会话结果"""
        logger.debug(f"查看 shell 会话内容: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"shell 会话不存在: {session_id}")
            raise NotFoundException(f"shell 会话不存在: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell.process

        raw_output = shell.output
        clean_output = self._remove_ansi_escape_codes(raw_output)

        if console:
            console_records = self.get_console_records(session_id)
        else:
            console_records = []
        
        return ShellViewResult(
            output=clean_output,
            session_id=session_id,
            console_records=console_records,
        )

    async def exec_command(
        self,
        session_id: str,
        exec_dir: str,
        command: str,
    ) -> ShellExecResult:
        """执行命令"""

        # 1. 记录日志并检查执行目录是否存在
        logger.info(f"正在会话 {session_id} 中执行命令: {command}")
        if not exec_dir or exec_dir == "" or exec_dir == "~":
            exec_dir = os.path.expanduser("~")
        
        if exec_dir.startswith("~"):
            exec_dir = exec_dir.replace("~", os.path.expanduser("~"), 1)
        
        if not os.path.exists(exec_dir):
            logger.error(f"当前目录不存在: {exec_dir}")
            return BadRequestException(f"当前目录不存在: {exec_dir}")

        try:
            # 2. 格式化并生成 ps1 路径
            ps1 = self._format_ps1(exec_dir)

            # 3. 判断当前 shell 会话是否存在
            if session_id not in self.active_shells:
                # 4. 创建一个新的进程
                logger.debug(f"创建一个新的 shell 会话: {session_id}")
                process = await self._create_process(exec_dir, command)
                self.active_shells[session_id] = Shell(
                    process=process,
                    exec_dir=exec_dir,
                    output="",
                    console_records=[ConsoleRecord(ps1=ps1, command=command, output="")]
                )

                # 5. 创建后台任务来运行输出读取器
                asyncio.create_task(self._start_output_reader(session_id, process))
            else:
                # 6. 该会话已存在，则读取数据
                logger.debug(f"使用现有的 shell 会话: {session_id}")
                shell = self.active_shells[session_id]
                old_process = shell.process

                # 7. 判断旧进程是否还在运行，如果是则先停止旧进程再执行新命令
                if old_process.returncode is None:
                    logger.debug(f"正在终止会话中的上一个进程: {session_id}")
                    try:
                        # 8. 结束旧进程并优雅等待 1s
                        old_process.terminate()
                        await asyncio.wait_for(old_process.wait(), timeout=1)
                    except Exception as e:
                        # 9. 结束旧进程出现错误并记录日志，调用 kill 强制关闭进程
                        logger.warning(f"强制终止 shell 会话中的进程: {session_id}，错误信息: {str(e)}")
                        old_process.kill()
                
                # 10. 关闭之后创建一个新的进程
                process = await self._create_process(exec_dir, command)
                
                # 11. 更新会话信息
                shell.process = process
                shell.exec_dir = exec_dir
                shell.output = ""
                shell.console_records.append(ConsoleRecord(ps1=ps1, command=command, output=""))

                # 12. 创建后台任务来运行输出读取器
                asyncio.create_task(self._start_output_reader(session_id, process))
        
            try:
                # 13. 尝试等待子进程执行（5s）
                logger.debug(f"正在等待会中的进程完成: {session_id}")
                wait_result = await self.wait_for_process(session_id, seconds=5)

                # 14. 判断返回代码是否非空（已结束）则同步返回结果
                if wait_result.returncode is not None:
                    logger.debug(f"shell 会话进程已结束，代码: {wait_result.returncode}")
                    view_result = await self.view_shell(session_id)

                    return ShellExecResult(
                        session_id=session_id,
                        command=command,
                        status="completed",
                        returncode=wait_result.returncode,
                        output=view_result.output,
                    )
            except BadRequestException as e:
                logger.warning(f"进程在会话超时后仍在运行: {session_id}, err: {str(e)}")
                pass
            except Exception as e:
                logging.warning(f"等待进程时出现异常: {str(e)}")
                pass

            return ShellExecResult(
                session_id=session_id,
                command=command,
                status="running",
            )
        except Exception as e:
            logger.error(f"执行命令[{command}]出现异常: {str(e)}", exc_info=True)
            raise AppException(
                msg=f"命令执行失败: {str(e)}",
                data={"session_id": session_id, "command": command}
            )
    
    async def write_to_process(
        self,
        session_id: str,
        input_text: str,
        press_enter: bool,
    ) -> ShellWaitResult:
        """根据传递的数据向指定子进程写入数据"""
        logger.debug(f"写入 shell 会话中的子进程: {session_id}，是否按下回车键: {press_enter}")
        if session_id not in self.active_shells:
            logger.error(f"shell 会话不存在: {session_id}")
            raise NotFoundException(f"shell 会话不存在: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell.process

        try:
            if process.returncode is not None:
                logger.error(f"子进程已结束，无法写入输入: {session_id}")
                raise BadRequestException(f"子进程已结束，无法写入输入: {session_id}")

            if sys.platform == "win32":
                encoding = locale.getpreferredencoding()
                line_ending = "\r\n"
            else:
                encoding = "utf-8"
                line_ending = "\n"
            
            text_to_send = input_text
            if press_enter:
                text_to_send += line_ending
            
            input_data = text_to_send.encode(encoding=encoding)
            log_text = input_text + ("\n" if press_enter else "")
            shell.output += log_text
            if shell.console_records:
                shell.console_records[-1].output += log_text

            # 向子进程写入数据
            process.stdin.write(input_data)
            await process.stdin.drain()

            logger.info("成功向子进程写入数据")
            return ShellWriteResult(status="success")
        except UnicodeError as e:
            logger.error(f"编码错误: {str(e)}")
            raise AppException(f"编码错误: {str(e)}")
        except Exception as e:
            logger.error(f"向子进程写入数据出错: {str(e)}")
            raise AppException(f"向子进程写入数据出错: {str(e)}")

    async def kill_process(self, session_id: str) -> ShellKillResult:
        """关闭子进程"""
        logger.debug(f"正在终止 shell 会话中的子进程: {session_id}")
        if session_id not in self.active_shells:
            logger.error(f"shell 会话不存在: {session_id}")
            raise NotFoundException(f"shell 会话不存在: {session_id}")
        
        shell = self.active_shells[session_id]
        process = shell.process

        try:
            if process.returncode is None:
                logger.info(f"尝试优雅终止进程: {session_id}")
                process.terminate()

                try:
                    await asyncio.wait_for(process.wait(), timeout=3)
                except asyncio.TimeoutError:
                    # 优雅关闭失败，则强制关闭
                    logger.warning(f"尝试强制关闭进程: {session_id}")
                    process.kill()

                logger.info(f"进程已终止，返回代码为: {process.returncode}")
                return ShellKillResult(status="terminated", returncode=process.returncode)
            else:
                logger.info(f"进程已终止，无需重复终止: {session_id}, 代码: {process.returncode}")
                return ShellKillResult(
                    status="already_terminated",
                    returncode=process.returncode,
                )
        except Exception as e:
            logger.error(f"关闭子进程异常: {str(e)}", exc_info=True)
            raise AppException(f"关闭子进程异常: {str(e)}")