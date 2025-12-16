# 自定义 Skill 实战教程

手把手教你创建一个完整的自定义 skill。

## 实战案例：创建天气查询 Skill

### 目标

创建一个可以查询城市天气的 skill，包含：
- Skill manifest 定义
- HTTP 服务实现
- 完整的测试流程

---

## 步骤 1: 创建 Manifest

创建文件 `skills/weather-query.yaml`:

```yaml
name: weather-query
description: "查询城市天气信息。Triggers on: weather, forecast, temperature, 天气, 气温, 温度, 预报"

inputs:
  - type: text
    description: "城市名称"

outputs:
  - type: text
    description: "天气信息"
  - type: json
    description: "详细天气数据"

runtime:
  type: service
  endpoint: http://localhost:8001/weather
  timeout: 30
  env:
    WEATHER_API_KEY: "demo-key"

tags:
  - weather
  - utility
  - real-time

metadata:
  version: "1.0.0"
  author: "SkillsLike Team"
  description_cn: "实时天气查询服务"
```

### 关键点解析

1. **关键词设计**:
   - 中文: 天气、气温、温度、预报
   - 英文: weather, forecast, temperature
   - 覆盖常见的用户表达方式

2. **Runtime 配置**:
   - `type: service` - 使用 HTTP 服务
   - `endpoint` - 本地服务地址（稍后创建）
   - `timeout: 30` - 30 秒超时（天气 API 通常很快）

---

## 步骤 2: 实现天气服务

创建 `services/weather_service.py`:

```python
"""天气查询服务示例."""

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Weather Query Service")


class WeatherRequest(BaseModel):
    """天气查询请求."""

    message: str  # 用户消息，包含城市名
    thread_id: str | None = None


class WeatherResponse(BaseModel):
    """天气查询响应."""

    text: str  # 文本描述
    file_id: str | None = None  # 文件 ID（可选）
    data: dict[str, Any] | None = None  # 额外数据


def extract_city(message: str) -> str:
    """从消息中提取城市名.

    简单实现：提取最后一个词作为城市名
    生产环境应使用 NLP 提取
    """
    # 移除常见的天气相关词汇
    words_to_remove = ["天气", "气温", "温度", "预报", "查询", "的", "weather", "forecast"]

    words = message.split()
    for word in words_to_remove:
        message = message.replace(word, "")

    city = message.strip()

    # 默认城市
    if not city:
        city = "北京"

    return city


async def query_weather(city: str) -> dict[str, Any]:
    """查询天气信息.

    这里使用模拟数据，实际应调用真实的天气 API
    例如: OpenWeatherMap, 和风天气等
    """
    # 模拟数据
    weather_data = {
        "北京": {"temp": 15, "condition": "晴", "humidity": 45, "wind": "3级"},
        "上海": {"temp": 20, "condition": "多云", "humidity": 60, "wind": "2级"},
        "深圳": {"temp": 25, "condition": "阴", "humidity": 70, "wind": "1级"},
        "成都": {"temp": 18, "condition": "小雨", "humidity": 80, "wind": "2级"},
    }

    # 默认数据
    default_weather = {"temp": 22, "condition": "未知", "humidity": 50, "wind": "1级"}

    return weather_data.get(city, default_weather)


@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest) -> WeatherResponse:
    """天气查询端点.

    Args:
        request: 包含用户消息的请求

    Returns:
        天气信息响应
    """
    try:
        # 提取城市名
        city = extract_city(request.message)

        # 查询天气
        weather = await query_weather(city)

        # 构建响应文本
        text = (
            f"📍 {city}的天气情况：\n\n"
            f"🌡️ 温度: {weather['temp']}°C\n"
            f"☁️ 天气: {weather['condition']}\n"
            f"💧 湿度: {weather['humidity']}%\n"
            f"💨 风力: {weather['wind']}\n"
        )

        return WeatherResponse(
            text=text,
            file_id=None,
            data={
                "city": city,
                "weather": weather,
                "source": "weather-query-skill"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询天气失败: {str(e)}"
        ) from e


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "healthy", "service": "weather-query"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 代码说明

1. **提取城市名**: 简单的字符串处理，生产环境应使用 NER
2. **查询天气**: 使用模拟数据，实际应调用真实 API
3. **响应格式**: 符合 SkillsLike 的标准格式

---

## 步骤 3: 启动服务

### 3.1 创建依赖文件

`services/requirements.txt`:

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pydantic>=2.0.0
```

### 3.2 安装依赖

```bash
cd services
pip install -r requirements.txt
```

### 3.3 启动天气服务

```bash
# 在一个终端启动天气服务
python weather_service.py
```

输出:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8001
```

---

## 步骤 4: 测试服务

### 4.1 测试天气服务本身

```bash
# 测试健康检查
curl http://localhost:8001/health

# 测试天气查询
curl -X POST http://localhost:8001/weather \
  -H "Content-Type: application/json" \
  -d '{"message": "北京天气"}'
```

期望输出:
```json
{
  "text": "📍 北京的天气情况：\n\n🌡️ 温度: 15°C\n☁️ 天气: 晴\n💧 湿度: 45%\n💨 风力: 3级\n",
  "file_id": null,
  "data": {
    "city": "北京",
    "weather": {"temp": 15, "condition": "晴", "humidity": 45, "wind": "3级"},
    "source": "weather-query-skill"
  }
}
```

---

## 步骤 5: 集成到 SkillsLike

### 5.1 重载技能

```bash
# 在另一个终端重载 SkillsLike
curl -X POST http://localhost:8000/api/reload
```

### 5.2 验证技能已加载

```bash
curl http://localhost:8000/api/skills | grep "weather-query"
```

---

## 步骤 6: 端到端测试

### 6.1 通过 API 测试

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "查询上海的天气",
    "thread_id": "test-weather"
  }'
```

### 6.2 通过前端测试

1. 打开浏览器: http://localhost:8000
2. 在左侧技能列表中查看 `weather-query`
3. 在聊天框输入: "北京天气怎么样？"
4. 等待响应

期望看到：
- 左侧技能列表显示 weather-query
- 右侧对话显示天气信息

---

## 步骤 7: 调试和优化

### 7.1 查看路由日志

观察 SkillsLike 服务器日志：

```
INFO - Chat request on thread test-weather: 查询上海的天气
INFO - Routed to 1 tools from 4 candidates for message: 查询上海的天气
INFO - Selected 1 tools for this request
```

### 7.2 测试关键词匹配

创建测试脚本 `test_routing.py`:

```python
from skillslike.router import IntentRouter
from skillslike.registry import SkillRegistry

# 加载技能
registry = SkillRegistry("skills/")
router = IntentRouter(registry.get_all_manifests())

# 测试不同的消息
test_messages = [
    "北京天气怎么样",
    "查询上海气温",
    "深圳的温度",
    "weather in Beijing",
]

for msg in test_messages:
    keywords = router._extract_keywords(msg)
    print(f"\n消息: {msg}")
    print(f"关键词: {keywords}")

    # 查看是否匹配 weather-query
    skill_keywords = router.get_skill_keywords("weather-query")
    matched = keywords & set(skill_keywords)
    print(f"匹配的关键词: {matched}")
```

运行:
```bash
python test_routing.py
```

### 7.3 优化关键词

如果发现匹配不准确，更新 manifest:

```yaml
description: "查询城市天气信息和预报。Triggers on: weather, forecast, temperature, climate, 天气, 气温, 温度, 预报, 气候, 怎么样, 如何"
```

---

## 步骤 8: 生产环境优化

### 8.1 集成真实天气 API

使用和风天气 API 示例:

```python
async def query_weather_real(city: str) -> dict[str, Any]:
    """调用真实的天气 API."""
    api_key = os.getenv("QWEATHER_API_KEY")

    # 1. 查询城市 ID
    async with httpx.AsyncClient() as client:
        geo_response = await client.get(
            "https://geoapi.qweather.com/v2/city/lookup",
            params={"location": city, "key": api_key}
        )
        geo_data = geo_response.json()
        location_id = geo_data["location"][0]["id"]

        # 2. 查询天气
        weather_response = await client.get(
            "https://devapi.qweather.com/v7/weather/now",
            params={"location": location_id, "key": api_key}
        )
        weather_data = weather_response.json()

        return {
            "temp": int(weather_data["now"]["temp"]),
            "condition": weather_data["now"]["text"],
            "humidity": int(weather_data["now"]["humidity"]),
            "wind": weather_data["now"]["windScale"] + "级"
        }
```

### 8.2 添加缓存

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 简单的内存缓存
weather_cache = {}

async def query_weather_cached(city: str) -> dict[str, Any]:
    """带缓存的天气查询."""
    now = datetime.now()

    # 检查缓存
    if city in weather_cache:
        cached_time, cached_data = weather_cache[city]
        if now - cached_time < timedelta(minutes=30):
            return cached_data

    # 查询并缓存
    weather = await query_weather_real(city)
    weather_cache[city] = (now, weather)

    return weather
```

### 8.3 错误处理

```python
@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest) -> WeatherResponse:
    """天气查询端点（生产版）."""
    try:
        city = extract_city(request.message)

        if not city:
            return WeatherResponse(
                text="❌ 请提供城市名称，例如：北京天气",
                file_id=None
            )

        weather = await query_weather_cached(city)

        text = format_weather_text(city, weather)

        return WeatherResponse(text=text, file_id=None, data={"city": city, "weather": weather})

    except httpx.HTTPError as e:
        return WeatherResponse(
            text=f"⚠️ 天气服务暂时不可用: {str(e)}",
            file_id=None
        )
    except KeyError as e:
        return WeatherResponse(
            text=f"❌ 无法找到城市 '{city}' 的天气信息",
            file_id=None
        )
    except Exception as e:
        logger.error(f"Weather query failed: {e}", exc_info=True)
        return WeatherResponse(
            text="❌ 查询失败，请稍后重试",
            file_id=None
        )
```

---

## 完整的项目结构

```
skillslike/
├── skills/
│   └── weather-query.yaml          # Skill manifest
├── services/
│   ├── weather_service.py          # 天气服务实现
│   └── requirements.txt            # 依赖
├── tests/
│   └── test_weather_skill.py       # 测试
└── skillslike/
    └── ...                         # 核心代码
```

---

## 总结

你已经学会了：

1. ✅ 创建 Skill Manifest
2. ✅ 实现 HTTP 服务
3. ✅ 集成到 SkillsLike
4. ✅ 测试和调试
5. ✅ 生产环境优化

### 下一步

- 🔄 尝试创建 Docker Runtime 的 skill
- 📊 添加数据可视化功能
- 🌐 集成更多外部 API
- 🧪 编写完整的测试套件

Happy Coding! 🚀
