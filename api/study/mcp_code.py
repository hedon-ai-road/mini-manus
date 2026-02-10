import os
import subprocess
import uuid
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="代码解释器",
    port=9888,
)

RUN_DIR = "/Users/hedon/mycode/python/mini-manus/api"
BASE_DIR = os.path.join(RUN_DIR, "temp")
UV_CMD = "uv"
NODE_CMD = "node"

@mcp.tool()
async def run_code(language: str, code: str, timeout: int = 30) -> str:
    """根据语言运行代码并返回执行结果，
    Python 代码会使用 /Users/hedon/mycode/python/mini-manus/api 中 uv 创建的 python3.10 版本运行。

    Args:
        language (str): 'python' 或者 'node'
        code (str): 要执行的代码文本
        timeout (int, optional): 最长运行秒数，默认为 30s.

    Returns:
        str: 执行输出(stdout)或错误信息(stderr/异常)
    """
    language = (language or '').strip().lower()
    if language not in ("python", "node"):
        return f"不支持的语言：{language}"

    suffix = ".py" if language == "python" else ".js"
    name = f"temp_{uuid.uuid4().hex}{suffix}"
    tmp_path = os.path.join(BASE_DIR, name)
    os.makedirs(BASE_DIR, exist_ok=True)

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        cwd = RUN_DIR
        if language == "python":
            cmd = [UV_CMD, "--directory", BASE_DIR, "run", name]
        else:
            cmd = [NODE_CMD, tmp_path]
        
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        if proc.returncode == 0:
            return stdout
        else:
            return f"命令返回非零状态 {proc.returncode}, stderr: \n{stderr or stdout}"
    except subprocess.TimeoutExpired:
        return f"执行超时(>{timeout}s)"
    except FileNotFoundError as e:
        return f"命令未找到，路径错误：{str(e)}"
    except Exception as e:
        return f"执行异常：{str(e)}"
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

if __name__ == "__main__":
    mcp.run(transport="streamable-http")