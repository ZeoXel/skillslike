# SkillsLike 前端

简洁美观的 Web 界面，用于测试 SkillsLike Agent。

## 功能

- ✅ 实时对话界面
- ✅ 技能列表展示
- ✅ 会话管理
- ✅ 文件下载支持
- ✅ 响应式设计
- ✅ 状态指示器

## 技术栈

- **HTML5** + **Tailwind CSS** - 现代化 UI
- **Vanilla JavaScript** - 无框架依赖
- **Fetch API** - HTTP 请求

## 使用方法

1. 启动 API 服务器：
   ```bash
   make run
   ```

2. 打开浏览器访问：
   ```
   http://localhost:8000
   ```

3. 开始对话！

## 界面说明

### 左侧面板 - 可用技能
- 显示所有已加载的技能
- 包含技能名称、描述、运行时类型和标签
- 点击"刷新技能"重新加载

### 右侧面板 - 对话界面
- 输入框：输入你的问题或指令
- 消息历史：显示对话记录
- 会话 ID：当前对话的唯一标识
- 清空对话：重置对话历史

## 示例对话

尝试以下消息：
- "分析这个表格数据"
- "帮我搜索 LangChain 的最新信息"
- "总结这个文档"
- "重组这些知识点"

## 自定义

要修改外观，编辑：
- `index.html` - HTML 结构
- `js/app.js` - 应用逻辑
- Tailwind classes - 样式

## 开发

在开发模式下运行：
```bash
uvicorn skillslike.api.main:app --reload
```

前端会自动连接到 `http://localhost:8000`。
