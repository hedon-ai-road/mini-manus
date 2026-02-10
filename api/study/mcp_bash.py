import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Bash工具")

@mcp.tool()
async def bash(command: str) -> dict:
    """传递 command 命令，在 Mac 下执行 shell 命令。

    Args:
        command (str): 需要执行的 command 命令

    Returns:
        dict: 返回命令的执行状态、结果、错误信息
    """
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")