# 🔌 Z.ai Integration - API-DISANO

> **Version:** 1.0
> **Date:** 2026-07-08
> **Status:** ✅ Configured
> **Provider:** Z.ai

---

## 📋 Overview

Z.ai is the primary LLM provider for API-DISANO, configured via Pi settings and integrated across the project for AI-powered features.

---

## ⚙️ Configuration

### Pi Settings

**File:** `.pi/settings.json`

```json
{
  "llmProvider": {
    "name": "z.ai",
    "config": {
      "enabled": true,
      "models": {
        "default": "zai-sonnet",
        "fast": "zai-haiku",
        "code": "zai-sonnet",
        "reasoning": "zai-opus"
      },
      "features": {
        "streaming": true,
        "functionCalling": true,
        "jsonMode": true,
        "temperature": 0.7
      }
    }
  }
}
```

### Environment Variables

**File:** `.env`

```bash
# Z.ai Configuration
ZAI_API_KEY=your-zai-api-key-here
ZAI_API_ENDPOINT=https://api.z.ai/v1
ZAI_MODEL_DEFAULT=zai-sonnet
ZAI_TEMPERATURE=0.7
ZAI_MAX_TOKENS=4096
ZAI_STREAMING=true
```

---

## 🤖 Available Models

| Model Name | Use Case | Characteristics |
|------------|----------|------------------|
| **zai-sonnet** | Default, Code, General tasks | Balanced reasoning + speed, 200k context |
| **zai-haiku** | Fast responses, Simple queries | Ultra-fast, cost-effective |
| **zai-opus** | Deep analysis, Complex reasoning | Maximum intelligence, slower |

### Model Selection Guidelines

```python
# Use zai-sonnet for:
- Code generation
- General API responses
- Documentation writing
- Test generation
- Refactoring suggestions

# Use zai-haiku for:
- Quick health checks
- Simple status queries
- Fast completions
- Low-latency requirements

# Use zai-opus for:
- Complex architectural decisions
- Deep security analysis
- Multi-step reasoning
- Code review with deep analysis
- Migration planning
```

---

## 🎯 Use Cases in API-DISANO

### 1. BC3 Description Generation

**Endpoint:** `POST /api/ai/bc3/generate-description`

**Purpose:** Generate BC3 descriptions for products using AI

**Configuration:**

```python
from app.services.ai_service import AIService

ai_service = AIService()
description = ai_service.generate_bc3_description(
    product_data={
        "codigo": "33036139",
        "descripcion": "Lámpara LED Disano...",
        "familia": "Iluminación"
    },
    model="zai-sonnet",
    temperature=0.7
)
```

### 2. Code Review and Analysis

**Purpose:** Analyze code changes for security vulnerabilities and code quality

**Configuration:**

```python
from app.services.ai_service import AIService

ai_service = AIService()
analysis = ai_service.analyze_code(
    code=file_contents,
    file_path="app/security/api_key.py",
    model="zai-opus",  # Deep analysis
    context="security-focused"
)
```

### 3. Test Generation

**Purpose:** Generate test cases for endpoints

**Configuration:**

```python
from app.services.ai_service import AIService

ai_service = AIService()
tests = ai_service.generate_tests(
    endpoint="POST /api/admin/productos",
    model="zai-sonnet",
    framework="pytest",
    patterns=["AAA", "negative-authorization"]
)
```

### 4. Documentation Generation

**Purpose:** Generate API documentation, migration guides

**Configuration:**

```python
from app.services.ai_service import AIService

ai_service = AIService()
docs = ai_service.generate_documentation(
    source="app/models.py",
    format="markdown",
    model="zai-sonnet"
)
```

---

## 🔌 Integration with Pi

### Pi Subagent Configuration

Z.ai is automatically used by Pi subagents when:

1. **Code Analysis:** `subagent run agent="code-reviewer"`
2. **Documentation:** `subagent run agent="doc-writer"`
3. **Testing:** `subagent run agent="test-generator"`
4. **Refactoring:** `subagent run agent="refactor-assistant"`

### Model Routing

Pi automatically selects models based on task complexity:

```python
# Simple tasks → zai-haiku
# Medium tasks → zai-sonnet
# Complex tasks → zai-opus
```

---

## 🛡️ Security Considerations

### API Key Management

- Store `ZAI_API_KEY` in `.env` (NEVER commit)
- Rotate keys quarterly
- Use read-only keys when possible
- Monitor usage logs

### Rate Limiting

- Z.ai API: 1000 requests/minute (adjust based on plan)
- Implement caching for repeated requests
- Use streaming for long responses

### Data Privacy

- Never send sensitive data (passwords, API keys) to Z.ai
- Anonymize product data before processing
- Store generated descriptions in database (cache)
- Comply with GDPR and data protection laws

---

## 📊 Usage Monitoring

### Metrics to Track

```python
from app.services.monitoring import track_zai_usage

# Track API calls
track_zai_usage(
    model="zai-sonnet",
    endpoint="/api/ai/bc3/generate-description",
    tokens_used=1500,
    cost=0.003
)
```

### Dashboard Metrics

- Total API calls per model
- Average tokens per request
- Cost per day/week/month
- Error rates by model
- Latency by model

---

## 🚀 Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
from app.config import get_settings

@lru_cache(maxsize=1000)
def get_cached_bc3_description(producto_id: str) -> str:
    """Cache BC3 descriptions for 24 hours"""
    # Check cache first
    # If not cached, call Z.ai
    # Store in cache
    # Return description
```

### Streaming Responses

```python
from app.services.ai_service import AIService

ai_service = AIService()
for chunk in ai_service.stream_bc3_description(
    product_id="33036139",
    model="zai-sonnet"
):
    # Process chunk in real-time
    print(chunk, end="", flush=True)
```

---

## 🧪 Testing with Z.ai

### Mocking Z.ai for Tests

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_zai_response():
    return {
        "bc3_descripcion_corta": "Lámpara LED 12W E27",
        "bc3_descripcion_larga": "Lámpara LED de 12W con base E27, color blanco cálido, ideal para iluminación general.",
        "bc3_product_type": "Lámpara LED"
    }

def test_generate_bc3_description(mock_zai_response):
    with patch('app.services.ai_service.ZaiClient.generate') as mock:
        mock.return_value = mock_zai_response
        
        result = ai_service.generate_bc3_description(producto_id="33036139")
        
        assert result["bc3_descripcion_corta"] == "Lámpara LED 12W E27"
        mock.assert_called_once()
```

---

## 📚 Related Documentation

- **Z.ai API Documentation:** [https://docs.z.ai](https://docs.z.ai)
- **Pi LLM Integration:** `.pi/settings.json`
- **AI Service:** `app/services/ai_service.py` (to be created)
- **BC3 Generation:** `app/services/bc3_service.py`

---

## 🔄 Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-07-08 | Initial configuration | Eloy Martínez Cuesta |

---

**Last updated:** 2026-07-08
**Status:** ✅ Active - Ready for use
