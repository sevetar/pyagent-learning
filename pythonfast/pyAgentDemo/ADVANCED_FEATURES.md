# LangChain 高级功能文档

本文档详细介绍了基于 LangChain 官方文档实现的三大高级功能。

## 目录

1. [Runtime Context（运行时上下文）](#runtime-context)
2. [Context Engineering（上下文工程）](#context-engineering)
3. [Guardrails（防护措施）](#guardrails)

---

## Runtime Context（运行时上下文）

### 概述

Runtime Context 提供**依赖注入**机制，允许在运行时传递静态配置信息（如用户 ID、数据库连接、权限等），而不是硬编码或使用全局状态。

### 实现

```python
from dataclasses import dataclass

@dataclass
class UserContext:
    """用户运行时上下文"""
    user_id: str
    user_name: str
    user_role: str  # admin, editor, viewer
    language: str = "zh"
    max_tokens_per_request: int = 2000

# 使用
context = UserContext(
    user_id="user_001",
    user_name="张三",
    user_role="admin",
    language="zh"
)

response = agent.chat("你好", context)
```

### 特点

- **会话级别的配置**：在整个对话中保持不变
- **依赖注入**：工具和中间件可以访问上下文
- **类型安全**：使用 dataclass 定义结构
- **灵活性**：可以包含任何静态配置

### 使用场景

- 用户身份和权限管理
- 数据库连接配置
- API 密钥管理
- 多语言支持
- 环境配置（开发/生产）

---

## Context Engineering（上下文工程）

### 概述

Context Engineering 是提供正确的信息和工具，使 LLM 能够完成任务的核心技术。包括：

1. **Model Context**：控制发送给模型的内容
2. **Tool Context**：控制工具的访问和输出
3. **Life-cycle Context**：控制代理生命周期中的行为

### 1. Dynamic Prompts（动态提示）

根据用户上下文动态生成系统提示。

```python
def _get_dynamic_system_prompt(self, context: UserContext) -> str:
    """根据用户上下文生成动态系统提示"""
    base_prompt = "你是一个智能助手。"

    # 根据用户角色调整
    if context.user_role == "admin":
        base_prompt += "\n你拥有管理员权限，可以执行所有操作。"
    elif context.user_role == "editor":
        base_prompt += "\n你拥有编辑权限，可以查询和修改数据。"
    elif context.user_role == "viewer":
        base_prompt += "\n你只有查看权限，只能执行只读操作。"

    # 根据语言调整
    if context.language == "en":
        base_prompt = "You are an intelligent assistant..."

    return base_prompt
```

**特点：**
- 基于用户角色定制提示
- 支持多语言
- 动态调整行为

### 2. Dynamic Tool Selection（动态工具选择）

根据用户权限动态过滤可用工具。

```python
def _filter_tools_by_role(self, context: UserContext) -> list:
    """根据用户角色过滤可用工具"""
    allowed_tools = ALL_TOOLS.copy()

    if context.user_role == "viewer":
        # 查看者只能使用只读工具
        allowed_tools = [
            tool for tool in allowed_tools
            if tool.name in ["get_weather", "get_current_time"]
        ]
    elif context.user_role == "editor":
        # 编辑者可以使用大部分工具
        allowed_tools = [
            tool for tool in allowed_tools
            if tool.name != "delete_data"
        ]
    # admin 可以使用所有工具

    return allowed_tools
```

**特点：**
- 基于角色的访问控制（RBAC）
- 动态工具过滤
- 安全性增强

### 3. Context-aware Messages（上下文感知消息）

根据对话状态动态调整消息内容。

```python
# 示例：根据对话长度调整提示
message_count = len(state["messages"])
if message_count > 10:
    base_prompt += "\n这是一个长对话 - 请保持简洁。"
```

**特点：**
- 对话状态感知
- 自适应行为
- 优化用户体验

---

## Guardrails（防护措施）

### 概述

Guardrails 是保护系统安全和合规的关键机制，包括：

1. **输入验证**：检查用户输入
2. **输出过滤**：清理敏感信息
3. **内容审核**：阻止不当内容

### 1. Content Filtering（内容过滤）

检测和阻止不当内容。

```python
def _apply_guardrails(self, message: str, context: UserContext) -> tuple[bool, str]:
    """应用防护措施"""
    if not self.enable_guardrails:
        return True, ""

    # 1. 内容过滤 - 检查禁用关键词
    banned_keywords = ["hack", "exploit", "malware", "virus"]
    message_lower = message.lower()
    for keyword in banned_keywords:
        if keyword in message_lower:
            return False, f"检测到不当内容关键词：{keyword}"

    # 2. 长度检查
    max_length = context.max_tokens_per_request * 4
    if len(message) > max_length:
        return False, f"消息过长，请限制在 {max_length} 字符以内"

    return True, ""
```

**特点：**
- 关键词黑名单
- 长度限制
- 实时检测

### 2. PII Detection（个人信息检测）

检测和处理个人身份信息。

```python
def _apply_guardrails(self, message: str, context: UserContext) -> tuple[bool, str]:
    """PII 检测（简化版）"""
    import re

    # 检测邮箱
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, message):
        print("[Guardrail] 检测到邮箱地址，已记录但允许继续")

    return True, ""

def _sanitize_output(self, output: str) -> str:
    """清理输出内容 - 隐藏邮箱"""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    output = re.sub(email_pattern, '[REDACTED_EMAIL]', output)
    return output
```

**特点：**
- 自动检测 PII
- 输出脱敏
- 合规保护

### 3. Role-based Access Control（基于角色的访问控制）

根据用户角色限制功能访问。

```python
# 在 _filter_tools_by_role 中实现
if context.user_role == "viewer":
    # 只允许只读操作
    allowed_tools = [tool for tool in tools if tool.name in READ_ONLY_TOOLS]
```

**特点：**
- 细粒度权限控制
- 防止未授权操作
- 安全性增强

---

## 完整示例

### 基础使用

```python
from agents import AdvancedAgent, UserContext

# 创建代理
agent = AdvancedAgent(enable_guardrails=True)

# 创建用户上下文
context = UserContext(
    user_id="user_001",
    user_name="张三",
    user_role="admin",
    language="zh"
)

# 对话
response = agent.chat("北京今天天气怎么样？", context)
print(response)
```

### 结构化分析

```python
# 获取结构化分析
response = agent.chat_with_analysis(
    "请分析一下人工智能在医疗领域的应用前景",
    context
)

print(f"摘要: {response.summary}")
print(f"关键要点: {response.key_points}")
print(f"置信度: {response.confidence}")
```

### 多角色演示

```python
# 管理员
admin_context = UserContext(
    user_id="admin_001",
    user_name="管理员",
    user_role="admin",
    language="zh"
)

# 查看者
viewer_context = UserContext(
    user_id="viewer_001",
    user_name="查看者",
    user_role="viewer",
    language="zh"
)

# 管理员可以使用所有工具
admin_response = agent.chat("帮我计算 100 + 200", admin_context)

# 查看者只能使用只读工具
viewer_response = agent.chat("帮我计算 100 + 200", viewer_context)
```

---

## 运行演示

### 基础演示
```bash
uv run main.py
```

### 增强功能演示
```bash
uv run demo_enhanced.py
```

### 高级功能演示
```bash
uv run demo_advanced.py
```

---

## 项目结构

```
pyAgentDemo/
├── config/
│   ├── __init__.py
│   └── settings.py           # 配置管理
├── tools/
│   ├── __init__.py
│   └── weather_tools.py      # 工具定义
├── agents/
│   ├── __init__.py
│   ├── weather_agent.py      # 基础代理
│   ├── enhanced_agent.py     # 增强代理（Memory, Streaming, Structured Output, Middleware）
│   └── advanced_agent.py     # 高级代理（Runtime, Context Engineering, Guardrails）
├── docs/
│   ├── runtime.txt           # Runtime 文档
│   ├── Context engineering.txt  # Context Engineering 文档
│   └── guardrails.txt        # Guardrails 文档
├── main.py                   # 基础演示
├── demo_enhanced.py          # 增强功能演示
├── demo_advanced.py          # 高级功能演示
├── .env                      # 环境变量
├── ENHANCED_FEATURES.md      # 增强功能文档
└── ADVANCED_FEATURES.md      # 本文档
```

---

## 功能对比

| 功能 | 基础代理 | 增强代理 | 高级代理 |
|------|---------|---------|---------|
| 工具调用 | ✅ | ✅ | ✅ |
| 对话记忆 | ✅ | ✅ | ✅ |
| 流式传输 | ❌ | ✅ | ❌ |
| 结构化输出 | ❌ | ✅ | ✅ |
| 中间件 | ❌ | ✅ | ❌ |
| Runtime Context | ❌ | ❌ | ✅ |
| 动态提示 | ❌ | ❌ | ✅ |
| 动态工具选择 | ❌ | ❌ | ✅ |
| 防护措施 | ❌ | ❌ | ✅ |
| 角色权限控制 | ❌ | ❌ | ✅ |

---

## 最佳实践

### 1. Runtime Context

- ✅ 使用 dataclass 定义上下文结构
- ✅ 只包含静态配置信息
- ✅ 避免在上下文中存储会话状态
- ❌ 不要在上下文中存储敏感信息（使用加密）

### 2. Context Engineering

- ✅ 根据用户角色动态调整提示
- ✅ 基于权限过滤工具
- ✅ 保持提示简洁明确
- ❌ 不要在提示中硬编码用户信息

### 3. Guardrails

- ✅ 分层防护（输入 + 输出）
- ✅ 记录所有安全事件
- ✅ 提供清晰的错误消息
- ❌ 不要过度限制合法用户

---

## 扩展开发

### 添加新的上下文字段

```python
@dataclass
class UserContext:
    user_id: str
    user_name: str
    user_role: str
    language: str = "zh"
    # 添加新字段
    department: str = ""
    cost_center: str = ""
```

### 添加新的防护规则

```python
def _apply_guardrails(self, message: str, context: UserContext):
    # 添加新的检查
    if context.department == "finance":
        # 金融部门的特殊规则
        if "transfer" in message.lower():
            return False, "金融操作需要额外审批"

    return True, ""
```

### 自定义工具权限

```python
TOOL_PERMISSIONS = {
    "admin": ["*"],  # 所有工具
    "editor": ["get_weather", "calculate", "get_current_time"],
    "viewer": ["get_weather", "get_current_time"]
}

def _filter_tools_by_role(self, context: UserContext):
    allowed_tool_names = TOOL_PERMISSIONS.get(context.user_role, [])
    if "*" in allowed_tool_names:
        return ALL_TOOLS

    return [t for t in ALL_TOOLS if t.name in allowed_tool_names]
```

---

## 常见问题

**Q: Runtime Context 和 State 有什么区别？**

A:
- Runtime Context：静态配置，整个会话不变（用户 ID、权限等）
- State：动态状态，每轮对话都可能改变（消息历史、上传文件等）

**Q: 如何实现更复杂的权限控制？**

A: 可以使用权限矩阵或 RBAC 库：

```python
PERMISSIONS = {
    "admin": {"tools": ["*"], "actions": ["read", "write", "delete"]},
    "editor": {"tools": ["get_weather", "calculate"], "actions": ["read", "write"]},
    "viewer": {"tools": ["get_weather"], "actions": ["read"]}
}
```

**Q: 如何持久化用户上下文？**

A: 可以使用数据库或缓存：

```python
# 从数据库加载
context = load_user_context_from_db(user_id)

# 使用
response = agent.chat(message, context)
```

**Q: 防护措施会影响性能吗？**

A:
- 简单的关键词检查：几乎无影响
- 正则表达式匹配：轻微影响
- LLM 安全检查：明显影响（建议异步或采样）

---

## 参考资料

- [LangChain Runtime 文档](https://docs.langchain.com/oss/python/langchain/runtime)
- [LangChain Context Engineering 文档](https://docs.langchain.com/oss/python/langchain/context-engineering)
- [LangChain Guardrails 文档](https://docs.langchain.com/oss/python/langchain/guardrails)
- [LangChain Middleware 文档](https://docs.langchain.com/oss/python/langchain/middleware)
