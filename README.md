# pymodbus 示例：本地 Modbus TCP 从站（模拟器）与轮询客户端

这是一个简单的示例集合，包含一个 Modbus TCP 从站（server.py）用于模拟寄存器数据，以及一个轮询客户端（client_poll.py）用于周期性读取保持寄存器并将结果写入 CSV（modbus_log.csv）。

文件说明
- server.py：Modbus TCP 从站（模拟器），监听 0.0.0.0:5020，会周期性更新部分保持寄存器以示例展示。
- client_poll.py：轮询客户端，每 N 秒读取若干保持寄存器并追加到 modbus_log.csv 中。
- requirements.txt：依赖列表（pymodbus）。

先决条件
- Python 3.8+
- 推荐使用虚拟环境（venv）来隔离依赖。

快速上手
1. 克隆仓库并切换到示例分支（仓库已在 add-modbus-examples 分支中添加示例文件）：
   git fetch origin
   git checkout add-modbus-examples

2. 创建并激活虚拟环境：
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate

3. 安装依赖：
   pip install -r requirements.txt

4. 启动从站（在一个终端）：
   python server.py

   说明：示例使用非特权端口 5020（避免需要管理员权限）。如果你希望监听标准 Modbus 502 端口，请注意需要管理员/root 权限并修改 server.py 中的端口。

5. 启动客户端（另一个终端）：
   python client_poll.py

   客户端默认每 2 秒读取一次保持寄存器（默认读取 4 个寄存器），并将数据追加到当前目录下的 modbus_log.csv 文件中。

注意事项与扩展建议
- 防火墙：若在远程主机或容器中运行，请确保 5020 端口对客户端可达或调整监听地址。
- 异步实现：当前示例使用同步 API（pymodbus.sync）。若你希望学习 asyncio 风格，可以把示例改为异步实现以支持更高并发。
- 可视化：可以用 matplotlib/plotly 或者 Flask + Chart.js 把 modbus_log.csv 可视化为实时仪表盘。
- 与真实设备对接：把客户端的 HOST、PORT 和 UNIT 修改为真实设备的值，并检查寄存器地址映射。

如何创建 Pull Request
仓库中的变更已提交到分支 `add-modbus-examples`。你可以访问下面的链接在网页上创建合并请求（Pull Request）：

https://github.com/sjysjy8868/pymodbus/compare/add-modbus-examples?expand=1

如果你希望我继续帮你创建 PR（如果有权限）或修改文件（例如改成 async 版本、添加更详细的中文说明、或把示例拆成更小的模块），告诉我我会继续操作。
