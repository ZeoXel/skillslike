# Nano-Banana-2 图像生成指南

## 🎨 功能概述

已成功添加基于 **nano-banana-2** 的 AI 图像生成技能！

### 技能信息
- **名称**: nano-banana-image-gen
- **模型**: nano-banana-2 (优化版 Gemini-2.5-flash-image-preview)
- **提供商**: bltcy.ai
- **特性**:
  - 🎯 4K 高清画质
  - 📐 多种比例支持 (1:1, 4:3, 16:9, 等)
  - ⚡ 快速生成
  - 💰 失败不扣费
  - 🖼️ 直接返回 URL

## 🚀 使用方法

### 方式 1: 通过前端界面

1. 访问 http://localhost:8000
2. 在聊天框输入图像描述
3. 系统会自动识别并使用图像生成技能

### 触发关键词

中文: `画`, `图片`, `生成`, `绘制`, `创建`
英文: `draw`, `image`, `picture`, `generate`, `create`

## 💬 测试示例

### 基础示例

```
帮我画一只猫
```

```
生成一幅山水画
```

```
Create an image of a sunset over the ocean
```

### 高级示例（带参数）

虽然当前通过聊天界面使用简化参数，但 API 支持：

- **比例**: 1:1, 4:3, 3:4, 16:9, 9:16, 2:3, 3:2, 4:5, 5:4, 21:9
- **尺寸**: 1K, 2K, 4K (默认 4K)
- **格式**: url, b64_json (默认 url)

### 创意提示词示例

```
画一个赛博朋克风格的未来城市，霓虹灯闪烁，高楼大厦
```

```
生成一幅水彩风格的森林场景，阳光透过树叶
```

```
创建一个可爱的卡通机器人，圆滚滚的身体，大眼睛
```

```
绘制一个中国传统山水画，水墨风格，远山近水
```

## 🔧 API 直接调用

### 使用 curl

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "画一只可爱的熊猫",
    "thread_id": "test-image-gen"
  }'
```

### 响应示例

```json
{
  "text": "图片生成成功！\n\n描述: 一只可爱的熊猫\n比例: 1:1\n分辨率: 4K\n\nfile_id: abc123...\n图片URL: https://...",
  "files": ["abc123..."],
  "thread_id": "test-image-gen"
}
```

## 📊 技术细节

### 实现架构

1. **Skill Manifest** (`skills/nano-banana-image-gen.yaml`)
   - 定义技能元数据和触发关键词
   - 配置运行时参数

2. **Image Gen Executor** (`skillslike/executors/image_gen_executor.py`)
   - 调用 bltcy.ai 的图像生成 API
   - 下载并存储生成的图片
   - 返回 file_id 和 URL

3. **前端增强** (`static/js/app.js`)
   - 自动识别图像生成响应
   - 内嵌显示生成的图片
   - 提供下载按钮

### API 端点

```
POST https://api.bltcy.ai/v1/images/generations

Headers:
  Authorization: Bearer {OPENAI_API_KEY}
  Content-Type: application/json

Body:
{
  "model": "nano-banana-2",
  "prompt": "描述文字",
  "aspect_ratio": "1:1",
  "image_size": "4K",
  "response_format": "url"
}
```

### 文件存储

生成的图片会：
1. 从 URL 下载
2. 存储到本地 `data/files/` 目录
3. 返回唯一的 `file_id`
4. 通过 `/api/file/{file_id}` 访问

## 🎯 前端展示

当收到图像生成结果时，前端会：
- ✅ 自动内嵌显示图片
- ✅ 支持点击放大查看
- ✅ 提供下载原图按钮
- ✅ 优雅的加载动画
- ✅ 响应式布局

## 🐛 故障排查

### 问题：图片生成失败

**检查项**:
1. API 密钥是否正确
2. 网络连接是否正常
3. 提示词是否符合内容政策

**查看日志**:
```bash
# 服务器会输出详细的调用日志
tail -f /tmp/claude/tasks/*.output
```

### 问题：图片无法显示

**解决方案**:
1. 检查 file_id 是否正确
2. 访问 `http://localhost:8000/api/file/{file_id}` 测试
3. 查看浏览器控制台错误

### 问题：生成速度慢

**说明**:
- nano-banana-2 4K 画质生成通常需要 10-30 秒
- 复杂场景可能需要更长时间
- 前端会显示"打字中"动画

## 📈 性能优化

### 当前实现
- ✅ 异步下载图片
- ✅ 错误处理和重试
- ✅ 超时控制 (60秒)
- ✅ 文件缓存

### 未来改进
- [ ] 图片压缩
- [ ] CDN 加速
- [ ] 批量生成
- [ ] 历史记录

## 🎨 创意提示

### 获得更好效果的技巧

1. **明确风格**: "水彩风格"、"油画风格"、"赛博朋克"
2. **详细描述**: 颜色、光线、构图、情绪
3. **添加元素**: 前景、背景、主体、细节
4. **使用形容词**: 可爱的、宏伟的、神秘的、温暖的

### 示例对比

❌ **模糊**: "一只猫"
✅ **清晰**: "一只橘色的小猫咪，坐在窗台上晒太阳，背景是模糊的城市天际线，暖色调，温馨氛围"

❌ **简单**: "风景"
✅ **丰富**: "日落时分的海边，金色阳光洒在波光粼粼的海面上，远处有几只海鸥飞翔，前景是细腻的沙滩"

## 📝 当前状态

### ✅ 已实现
- 完整的图像生成 API 集成
- 前端图片展示和下载
- 文件存储和管理
- 错误处理和日志

### 🔄 技能状态
- **加载状态**: ✅ 已加载
- **可用技能**: 4 个
  1. nano-banana-image-gen (新增)
  2. knowledge-reorganizer
  3. excel-analyzer
  4. web-search

---

**开始创作吧！** 🎨

在浏览器中访问 http://localhost:8000 并尝试：
```
帮我画一幅美丽的星空
```
