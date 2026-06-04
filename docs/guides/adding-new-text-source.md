<!-- 状态: active | 最后验证: 2026-06-04 -->
# 如何添加新的文本来源（Guide）

> 目标：添加一个从新位置加载文本的功能（如 PDF、Markdown、API 端点）。

---

## 步骤

### 1. 在 `ports/` 定义新 Port（如果现有 Port 不够用）

如果现有 `LocalTextLoader`、`TextProvider`、`Clipboard` 能覆盖你的场景，跳到这里。

```python
# ports/new_source.py
from abc import ABC, abstractmethod

class NewSourceProvider(Protocol):
    @abstractmethod
    def load_text(self, source_id: str) -> str: ...
    
    @abstractmethod
    def list_sources(self) -> list[TextCatalogItem]: ...
```

### 2. 在 `integration/` 实现 Port

```python
# integration/new_source_repository.py
from ports.new_source import NewSourceProvider

class NewSourceRepository(NewSourceProvider):
    def load_text(self, source_id: str) -> str:
        # 你的实现
        ...
    
    def list_sources(self) -> list[TextCatalogItem]:
        return [...]
```

### 3. 在 `config/text_source_config.py` 添加配置

```python
# config.example.json 新增
{
    "text_sources": {
        "new_source": {
            "type": "new_source",
            "enabled": true
        }
    }
}
```

### 4. 在 `text_source_gateway.py` 添加路由

```python
# 在 TextSourceGateway.plan_load() 中添加
elif plan.source_entry.source_key == "new_source":
    return self._route_to_new_source(plan)
```

### 5. 在 `main.py` / `container.py` 装配

```python
# container.py
new_source_repo = NewSourceRepository(runtime_config)
gateways.new_source = NewSourceGateway(new_source_repo, ...)
```

### 6. 写测试

```bash
# tests/test_new_source_repository.py
# tests/test_text_source_gateway.py  # 新增路由分支
```

### 7. 更新文档

- `docs/reference/api-endpoints.md`（如果涉及 API 端点）
- `CHANGELOG.md`（用户可见变更）

---

## 常见陷阱

1. **不要**在 Adapter 中做来源路由——路由在 Gateway 中
2. **不要**让 Port 依赖 Qt 类型——Port 是纯 Python 协议
3. **不要**在主线程加载文本——统一走 Worker
4. 新增 Port 后记得在 `container.py` 中正确装配
