# Supervisor

Supervisor 提供了一套非常强大的 XML-RPC 接口，允许开发者通过编程方式远程控制进程、获取日志和查看系统状态。

这些接口通常分为几个主要的命名空间，最常用的是 `supervisor` 命名空间。

---

### 1. 进程控制 (Process Control)

这些接口用于管理受控进程的生命周期。

| 接口名称                              | 功能说明                                           |
| :------------------------------------ | :------------------------------------------------- |
| `supervisor.startProcess(name, wait)` | 启动指定的进程。                                   |
| `supervisor.stopProcess(name, wait)`  | 停止指定的进程。                                   |
| `supervisor.startAllProcesses(wait)`  | 启动配置文件中的所有进程。                         |
| `supervisor.stopAllProcesses(wait)`   | 停止所有正在运行的进程。                           |
| `supervisor.restart()`                | 重启 Supervisor 守护进程（会导致所有子进程退出）。 |

### 2. 状态查询 (Status & Info)

用于获取当前进程的运行详情。

| 接口名称                          | 功能说明                                          |
| :-------------------------------- | :------------------------------------------------ |
| `supervisor.getProcessInfo(name)` | 获取单个进程的详细信息（状态、PID、运行时间等）。 |
| `supervisor.getAllProcessInfo()`  | 获取所有进程的状态列表。                          |
| `supervisor.getState()`           | 获取 Supervisor 自身的状态。                      |
| `supervisor.getPID()`             | 获取 Supervisor 进程的 PID。                      |

`ProcessInfo` 结构如下：

| **键名 (Key)**   | **类型** | **说明**                                   |
| ---------------- | -------- | ------------------------------------------ |
| **`name`**       | string   | 进程名称                                   |
| **`group`**      | string   | 进程组名称                                 |
| **`start`**      | int      | 进程启动的 UNIX 时间戳                     |
| **`stop`**       | int      | 进程停止的 UNIX 时间戳（未停止则为 0）     |
| **`now`**        | int      | 当前系统的 UNIX 时间戳                     |
| **`state`**      | int      | 状态代码（如 20 代表 RUNNING）             |
| **`statename`**  | string   | 状态文字描述（RUNNING, STOPPED, FATAL 等） |
| **`spawnerr`**   | string   | 启动时的错误信息（如果没有则为空）         |
| **`exitstatus`** | int      | 退出状态码                                 |
| **`pid`**        | int      | 进程的 PID（未运行则为 0）                 |
| **`logfile`**    | string   | stdout 日志文件的绝对路径                  |



### 3. 日志读取 (Log Management)

无需直接访问服务器文件系统即可读取输出日志。

- **`supervisor.readProcessStdoutLog(name, offset, length)`**: 读取指定进程的标准输出日志。
- **`supervisor.readProcessStderrLog(name, offset, length)`**: 读取指定进程的错误日志。
- **`supervisor.clearProcessLogs(name)`**: 清除指定进程的日志文件。
- **`supervisor.readLog(offset, length)`**: 读取 Supervisor 自身的系统日志。

### 4. 系统管理 (System Management)

用于动态调整配置或关闭服务。

- **`supervisor.reloadConfig()`**: 重新加载配置文件，识别更改。
- **`supervisor.addProcessGroup(name)`**: 动态添加进程组。
- **`supervisor.removeProcessGroup(name)`**: 从当前运行配置中移除进程组。
- **`supervisor.shutdown()`**: 关闭 Supervisor 及其所有子进程。

---

### 如何调用这些接口？

由于它们是标准的 **XML-RPC** 协议，你可以使用 Python 自带的库轻松调用。

> **注意：** 你需要在 `supervisord.conf` 中启用 `[inet_http_server]` 或 `[unix_http_server]` 才能使用 RPC。

```python
import xmlrpc.client

# 连接到 Supervisor (假设开启了 inet 端口 9001)
server = xmlrpc.client.ServerProxy('http://user:pass@localhost:9001/RPC2')

# 示例：获取所有进程状态
processes = server.supervisor.getAllProcessInfo()
for p in processes:
    print(f"Name: {p['name']}, State: {p['statename']}")

# 示例：重启某个进程
server.supervisor.stopProcess('my_app')
server.supervisor.startProcess('my_app')
```
