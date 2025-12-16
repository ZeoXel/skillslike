# SkillsLike 前端使用指南

## 🚀 快速开始

服务器已启动并运行在 `http://localhost:8000`

### 访问方式

在浏览器中打开以下任一地址：

1. **主界面**: http://localhost:8000
2. **API 文档**: http://localhost:8000/docs
3. **健康检查**: http://localhost:8000/health

## 📱 界面功能

### 左侧面板 - 可用技能

显示当前加载的 3 个示例技能：

1. **knowledge-reorganizer** (Docker)
   - 重组和总结文档
   - 关键词: 重组、梳理、总结

2. **excel-analyzer** (Anthropic)
   - 分析 Excel 表格
   - 关键词: 表格、分析、数据

3. **web-search** (Service)
   - 网络搜索
   - 关键词: 搜索、查找、查询

### 右侧面板 - 对话界面

- **输入框**: 输入你的问题
- **消息历史**: 显示对话记录
- **会话 ID**: 当前会话的唯一标识
- **清空对话**: 重置对话历史

## 💬 测试对话示例

尝试以下消息来测试不同的技能：

### 1. 测试 Excel 分析技能
```
分析这个表格数据
```

### 2. 测试网络搜索技能
```
搜索 LangChain 的最新信息
```

### 3. 测试文档重组技能
```
帮我总结这个文档
```

### 4. 通用对话
```
你好，你能做什么？
```

## 🎯 功能特性

### ✅ 已实现
- **实时对话**: WebSocket 风格的消息流
- **技能路由**: 根据关键词自动选择合适的技能
- **会话管理**: 每个会话独立的上下文
- **状态指示**: 实时显示连接状态
- **文件支持**: 如果有文件输出，会显示下载链接
- **响应式设计**: 支持桌面和移动设备

### 🎨 UI/UX 特点
- 现代化的渐变设计
- 流畅的动画效果
- 打字指示器
- 消息淡入动画
- 悬停效果

## 🔧 测试流程

### 1. 基础测试

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 获取技能列表
curl http://localhost:8000/api/skills

# 3. 发送消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "分析数据", "thread_id": "test-1"}'
```

### 2. 前端测试

1. 打开浏览器访问 http://localhost:8000
2. 查看左侧技能列表是否显示 3 个技能
3. 在右侧输入框输入消息
4. 观察消息发送和响应

### 3. 会话持久化测试

1. 发送消息："你好"
2. 发送消息："我刚才说了什么？"
3. 验证 Agent 是否记住上下文

## 📊 当前状态

### API 端点状态
- ✅ `GET /` - 前端页面
- ✅ `GET /health` - 健康检查
- ✅ `GET /api/skills` - 技能列表
- ✅ `POST /api/chat` - 对话接口
- ✅ `GET /api/file/{id}` - 文件下载
- ✅ `GET /docs` - API 文档

### 技能加载状态
- ✅ 3 个示例技能已加载
- ✅ 路由器已初始化
- ✅ 文件存储已就绪

## 🐛 故障排查

### 问题：无法连接到服务器
**解决方案**:
```bash
# 检查服务器是否运行
curl http://localhost:8000/health

# 如果未运行，启动服务器
uv run uvicorn skillslike.api.main:app --reload
```

### 问题：技能列表为空
**解决方案**:
```bash
# 检查 skills/ 目录
ls skills/examples/

# 重新加载技能
curl -X POST http://localhost:8000/api/reload
```

### 问题：消息发送失败
**检查**:
1. `.env` 文件中的 API 密钥是否正确
2. 网络连接是否正常
3. 查看浏览器控制台错误

## 🔄 开发模式

### 启动开发服务器
```bash
# 自动重载模式
make run
# 或
uvicorn skillslike.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 查看日志
服务器日志会显示：
- 加载的技能数量
- 每次请求的路由信息
- 选择的工具
- API 调用详情

### 修改前端
编辑以下文件后刷新浏览器即可：
- `static/index.html` - HTML 结构
- `static/js/app.js` - JavaScript 逻辑

## 📈 下一步

### 功能扩展建议
1. ✅ 添加文件上传功能
2. ✅ 实现语音输入
3. ✅ 添加代码高亮显示
4. ✅ 支持 Markdown 渲染
5. ✅ 添加对话导出功能

### 性能优化
1. ✅ 实现消息分页
2. ✅ 添加虚拟滚动
3. ✅ 缓存技能列表
4. ✅ WebSocket 实时通信

## 📝 API 配置说明

当前配置使用第三方 API 供应商：
```bash
# .env
OPENAI_API_KEY=sk-JO438PQ5WpZFtR9Gt5tMN119FmD1bG6YDtmczNgGyDIMCHc1
OPENAI_BASE_URL=https://api.bltcy.ai/v1
USE_OPENAI_COMPATIBLE=true
```

所有对话将通过配置的端点路由。

---

**开始测试吧！** 🎊

打开浏览器访问: http://localhost:8000
