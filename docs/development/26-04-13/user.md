- [x] create a command, user can config providers
- [x] create a command, user can config persona

- [ ] create a plugin debug workflow

- [x] ## system

此命令组用于管理 Astrbot 自身，使用 pm2 管理 astrbot 进程

| 子命令 | 功能 |
|--------|------|
| `init` | 初始化 AstrBot 环境（生成配置、安装依赖等），对应现有 `astrbot init` 的行为。 |
| `upgrade` | 升级 AstrBot 本身（如 `uv tool upgrade astrbot`）。 |
| `start` | 启动 AstrBot 服务（如果 CLI 负责管理后台进程）。 |
| `stop` | 停止运行中的 AstrBot 服务。 |
| `restart` | 重启服务。 |
| `status` | 查看 AstrBot 服务运行状态（PID、端口、健康检查等）。 |
| `logs` | 查看 AstrBot 运行日志，支持 `--follow`、`--lines` 等参数。 |
| `info` 或 `version` | 显示 AstrBot 版本、安装路径、Python 环境等信息。 |
