# TVBox AI 多租户控制中心

FastAPI 控制中心通过 WebSocket 连接 TVBox，使用 LLM Agent 或本地规则生成 Tool 指令。平台采用两条鉴权链路：Web 控制台和 `/api/v1/**` 使用用户 JWT；TVBox、`/v1/models` 和 `/v1/chat/completions` 使用数据库中的用户级 API Key。设备请求不提交 `user_id`，服务端通过 API Key 映射并强制执行租户过滤。

## 运行要求

- Python 3.9+
- MongoDB 6+（生产环境必须配置；未配置 `MONGO_URI` 时使用仅供本地演示的内存仓储）

```bash
python3 -m pip install -r requirements.txt
```

创建 `.env`：

```dotenv
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DATABASE=tvbox_ai
JWT_SECRET=replace-with-at-least-32-random-bytes
API_KEY_PEPPER=replace-with-an-independent-random-secret
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://your-console.example.com

# 首次启动时创建管理员；创建完成后可从环境中移除密码
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=ChangeThisPassword123!

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
SERVER_PORT=8000
```

启动：

```bash
python3 server.py
```

也可以使用本地持久化 Docker Compose 部署：

```bash
docker compose up -d --build
docker compose ps
```

打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)，登录后绑定设备。首次绑定会显示一次完整的用户级 API Key；同一用户的多台 TVBox 共用这个 Key。

## TVBox 模拟器

先在 Web 控制台绑定 `tvbox_01`，再配置：

```dotenv
TVBOX_DEVICE_ID=tvbox_01
TVBOX_API_KEY=sk-tvbox-copy-the-one-time-value
TVBOX_WS_URL=ws://127.0.0.1:8000/ws/v1/tvbox/tvbox_01
```

```bash
python3 mock_tvbox.py
```

## 关键接口

平台用户接口使用 `Authorization: Bearer <JWT>`：

- `POST /api/v1/auth/register`、`POST /api/v1/auth/login`
- `GET|POST /api/v1/invite/*`
- `GET|POST|PUT|DELETE /api/v1/devices/*`
- `GET /api/v1/api-key`、`POST /api/v1/api-key/reset`
- `/api/v1/admin/*`（仅 `ADMIN`）
- `POST /api/v1/chat/completions`（Web 控制台 JWT 适配接口）

设备接口使用 `Authorization: Bearer <用户级 API Key>`：

- `GET /v1/models`
- `POST /v1/chat/completions`
- `WS /ws/v1/tvbox/{device_id}`（兼容客户端也可使用脱敏日志环境下的 `?api_key=`）

设备侧请求不要发送 `user_id`。`model` 或 `device_id` 只用于在 API Key 映射用户的已绑定设备中选择目标。

## 测试

```bash
python3 -m unittest discover -v
python3 -m compileall -q app server.py langchain_agent.py mock_tvbox.py
```

测试覆盖 JWT、用户级 API Key 映射、跨租户设备隔离、设备全局唯一、WebSocket 绑定校验、Key 轮换和命令路由。
