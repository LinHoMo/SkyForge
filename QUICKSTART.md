# SkyForge 快速开始

跨平台，Windows / macOS / Linux 都能跑。

## 环境准备

```bash
# macOS 先装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install uv node@18 pnpm

# 想做真验证的话再装这几个，不装也行
brew install cppcheck cbmc z3
```

## 启动

```bash
cd SkyForge
sh start.sh
```

脚本会自己装依赖再把前后端拉起来。完了之后：

- 前端：http://localhost:5173
- API 文档：http://localhost:8000/docs
- 后端：http://localhost:8000

## 跑测试

```bash
uv run pytest src/skyforge_engine/tests/ -q

cd studio/frontend && pnpm test -- --run
```

## 开发模式

后端和前端分开起，都带热重载：

```bash
uv run uvicorn app.main:app --app-dir studio --reload

cd studio/frontend && pnpm dev
```

## 几个坑

- 第一次跑 `start.sh` 会建 `.venv`、装 `node_modules`，等一会
- Cppcheck / CBMC / Z3 缺了不会崩，自动退 mock 模式
- LLM 默认也是 mock，配了 API Key 才走真模型
- macOS 串口默认 `/dev/tty.usbserial`

更细的看 [USER_GUIDE.md](./docs/USER_GUIDE.md) 和 [ARCHITECTURE.md](./docs/ARCHITECTURE.md)。
