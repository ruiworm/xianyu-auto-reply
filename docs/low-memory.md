# 4GB / 单账号轻量部署

轻量模式保留自动回复、发货、账号管理、消息服务、定时任务和后台页面。主要减少数据库缓存、连接并发和未使用功能的启动依赖。它是低负载配置起点；内存峰值仍取决于浏览器、视频和批量任务。

## 本次代码优化

- OpenCV / NumPy 在提取视频封面时加载，未使用视频发布时不加载。
- Excel 依赖在导入、导出时加载，普通后台请求不加载。
- 验证码包按需导出各引擎；查询并发状态或滑块配置不再加载全部浏览器库，原有导出名、别名和统计单例保留。
- 数据库和 Redis 连接池允许设置为小于 600 的正整数。普通部署的默认值保留，轻量模式显式覆盖。

首次使用视频或 Excel 后，相关库通常会保留在 Python 进程中。这些修改主要降低未使用功能的启动及空闲内存。

## 先识别部署方式

在服务器执行只读命令：

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
docker compose ls
```

如果能看到 backend-web、websocket、scheduler、mysql 等容器，通常是 Docker 部署。没有 Docker 或由 `python main.py` / 启动器运行的服务，参考下方源码配置。此文档的操作在原部署目录执行，沿用原 Compose 项目名、环境文件与数据卷。

## Docker 源码部署

需要使用包含本次修改的源码构建三个后端。仅把轻量配置叠加到旧镜像上，旧代码会因连接池小于 600 而启动失败。

在仓库根目录先顺序构建，避免 4GB 机器同时构建多个镜像的峰值：

```bash
(
  set -e
  for service in backend-web websocket scheduler frontend; do
    docker compose -f docker-compose.yml -f docker-compose.low-memory.yml build "$service"
  done
)
```

确认四项构建成功后启动：

```bash
docker compose -f docker-compose.yml -f docker-compose.low-memory.yml up -d
```

以后查看状态、日志或重启时继续带上这两个 `-f` 参数。原本使用 `-p`、`--env-file` 的部署继续保留它们。覆盖文件不更改服务名、端口、账号密码、数据库名称和数据卷。

一键部署生成的 `docker-compose.deploy.yml` 使用预构建镜像，需要先更新对应镜像中的应用代码，不能直接照搬上述源码构建命令。外部 MySQL / Redis 部署不应叠加这个完整覆盖文件；只应用下方应用进程参数，数据库参数由外部数据库管理员调整。

| 项目 | 普通配置 | 轻量配置 |
| --- | --- | --- |
| 每个 Python 服务的数据库常驻连接上限 | 800 | 5 |
| 每个服务的临时溢出连接上限 | 30～150 | 5 |
| 每个服务的 Redis 连接上限 | 800 | 20 |
| MySQL 最大连接数 | 4000 | 100 |
| MySQL InnoDB 缓冲池 | 镜像默认值 | 64MB |
| MySQL Performance Schema | 镜像默认值 | 关闭 |
| Redis 数据内存上限 | 256MB | 64MB |
| websocket 进程的滑块 / 浏览器任务共享槽位 | 3 | 1 |

三个 Python 主服务合计最多 30 条池连接，为兼容层、建表、管理操作等保留 MySQL 连接余量。浏览器槽位设为 1 会让共享该槽位的任务排队；视频发布等独立路径仍可能创建额外工作负载。

连接池按需创建连接，800 并不等于启动就占用 800 条连接；缩小上限主要限制繁忙时及并发后的连接驻留。Redis `maxmemory` 是数据内存上限，进程 RSS 还包含持久化、缓冲区和内存分配器开销。覆盖文件没有设置容易造成服务被杀死的固定容器内存硬上限。

关闭 Performance Schema 会减少数据库性能诊断数据，普通 SQL 和应用健康检查仍可使用。降低缓存容量可能增加磁盘读取；需要更多吞吐时可在原 `.env` 增加以下非敏感配置：

```dotenv
LOW_MEMORY_DB_POOL_SIZE=5
LOW_MEMORY_DB_MAX_OVERFLOW=5
LOW_MEMORY_REDIS_POOL_SIZE=20
LOW_MEMORY_MYSQL_MAX_CONNECTIONS=100
LOW_MEMORY_MYSQL_BUFFER_POOL_SIZE=64M
LOW_MEMORY_REDIS_MAXMEMORY=64mb
```

增大应用池时同步提高 MySQL 上限，覆盖所有服务、进程及管理连接。不要把 Redis 缓存当作持久数据库；轻量模式沿用原有 `allkeys-lru` 淘汰策略。

## 源码 / 进程部署

把以下应用参数加入三个后端实际读取的 `.env`，或在进程管理器中设置后重启服务。滑块并发参数设置在 websocket 服务即可。

```dotenv
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
REDIS_POOL_SIZE=20
MAX_CAPTCHA_CONCURRENT=1
SQL_ECHO=false
MALLOC_ARENA_MAX=2
OPENBLAS_NUM_THREADS=1
OMP_NUM_THREADS=1
```

后三个参数应在启动 Python 之前通过进程环境导出；仅由 Pydantic 读取 `.env` 不会把它们写入进程环境。Linux shell 示例：

```bash
export MALLOC_ARENA_MAX=2 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python main.py
```

MySQL / Redis 的进程配置需要单独应用覆盖文件中对应的服务参数；修改应用 `.env` 不会修改数据库进程的设置。生产前端使用现有 Nginx 静态构建，Vite 开发服务器只用于开发。

## 验证

```bash
python -m unittest discover -s checks -v
docker compose -f docker-compose.yml -f docker-compose.low-memory.yml ps
docker stats --no-stream
```

回归检查需要主后端的 Python 依赖、Docker CLI 和 Compose，覆盖三服务冷启动依赖、连接池校验、Compose 数据卷与凭据继承、四类 Excel 往返和真实视频封面生成。

检查 backend-web、websocket、scheduler 的 `/health`：除了 HTTP 状态，业务响应还应为 `success: true` 且 `data.database: connected`。前端入口的 `/api/v1/public/status` 应返回四服务在线，`totals_available` 和 `online_accounts_available` 均为 `true`。

当前云环境、相同 Python 3.12 依赖的单次冷启动导入对比（RSS，未运行账号或浏览器任务）：

| 服务 | 修改前 | 修改后 |
| --- | ---: | ---: |
| backend-web | 187.3 MiB | 130.6 MiB |
| websocket | 118.8 MiB | 106.4 MiB |
| scheduler | 116.2 MiB | 100.1 MiB |

这些是云环境的测量值，不是生产服务器的内存保证。共享库的 RSS 不能简单相加作为整机占用；实际部署后用 `docker stats` 或进程 PSS 观察空闲和工作时的峰值。带真实账号的自动回复、发货、登录及滑块流程还需要在实际部署中验证。

独立轻量实例还完成了三服务运行验证、90 次并发数据库健康请求、数据库连接池排队与回收、20 个并发 Redis 操作，以及含内部鉴权的公开状态查询。该测试中 MySQL 配置为 100 连接、64MB 缓冲池，最大实际连接数为 24，容器内存约为 231 MiB；测试数据库没有配置真实闲鱼账号。
