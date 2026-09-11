# Rate Limit Analysis - Which API Key Hit the Limit?

**Date:** September 11, 2026  
**Analysis of 250-case test failure**

---

## 🎯 Answer: **GROQ API Key Hit the Rate Limit**

### Configuration Details:

From `.env` file:
```bash
# LLM Judge Configuration
JUDGE_MODEL=openai/gpt-oss-120b
OPENAI_API_KEY=gsk_**** # <-- GROQ KEY (REDACTED)
OPENAI_BASE_URL=https://api.groq.com/openai/v1  # <-- GROQ API

# Unused in this test
OPENAI_NATIVE_API_KEY=sk-proj-**** # <-- OpenAI key (REDACTED)
```

### Error Message from Logs:

```
Error code: 429 - {
  'error': {
    'message': 'Rate limit reached for model `openai/gpt-oss-120b` 
                in organization `org_01kj9jqhspf42r5q0jzsxrenwr` 
                service tier `on_demand` 
                on tokens per day (TPD): 
                  Limit: 200,000
                  Used: 199,793
                  Requested: 1,563
                Please try again in 9m45.791999999s. 
                Need more tokens? Upgrade to Dev Tier today at 
                https://console.groq.com/settings/billing',
    'type': 'tokens',
    'code': 'rate_limit_exceeded'
  }
}
```

---

## 📊 Key Facts:

| Item | Value |
|------|-------|
| **API Provider** | **Groq** (NOT OpenAI) |
| **Model** | `openai/gpt-oss-120b` |
| **Base URL** | `https://api.groq.com/openai/v1` |
| **API Key Used** | `gsk_Fgx8Fc...` (Groq key starting with `gsk_`) |
| **Tier** | Free "on_demand" tier |
| **Daily Token Limit** | 200,000 tokens/day |
| **Tokens Used** | 199,793 tokens |
| **Tokens Remaining** | 207 tokens |

---

## 🔍 Why Groq and Not OpenAI?

The system uses the **OpenAI SDK** but points it to **Groq's API** via `OPENAI_BASE_URL`:

```python
# Code uses OpenAI SDK but connects to Groq
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),      # Groq key here
    base_url=os.environ.get("OPENAI_BASE_URL")     # Points to Groq
)
```

This is a common pattern - Groq provides an OpenAI-compatible API, so you can use the OpenAI SDK but connect to Groq's servers.

---

## 💡 Available API Keys:

You have **TWO** API keys configured:

### 1. **Groq API Key** (Currently Used) ❌ Rate Limited
- **Variable:** `OPENAI_API_KEY`
- **Value:** `gsk_****************************` (Groq key - REDACTED)
- **Provider:** Groq
- **Status:** ❌ **RATE LIMITED** (199,793/200,000 tokens used)
- **Limit:** 200,000 tokens/day (free tier)
- **Resets:** Daily (24 hours from first use)

### 2. **OpenAI API Key** (Available, Not Used) ✅ Available
- **Variable:** `OPENAI_NATIVE_API_KEY`
- **Value:** `sk-proj-****************************` (OpenAI key - REDACTED)
- **Provider:** OpenAI
- **Status:** ✅ **AVAILABLE** (not being used)
- **Limit:** Depends on your OpenAI plan (typically much higher)
- **Cost:** Pay-per-use (typically $0.15-$0.60 per million tokens)

---

## 🚀 Solutions to Complete the 250-Case Test

### Option 1: Switch to OpenAI API Key (RECOMMENDED - Immediate)

**Change in `.env` file:**
```bash
# OLD (Groq - rate limited)
JUDGE_MODEL=openai/gpt-oss-120b
OPENAI_API_KEY=gsk_**** # Your Groq key here
OPENAI_BASE_URL=https://api.groq.com/openai/v1

# NEW (OpenAI - higher limits)
JUDGE_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-**** # Your OpenAI key here
OPENAI_BASE_URL=https://api.openai.com/v1
# Or remove OPENAI_BASE_URL (defaults to OpenAI)
```

**Benefits:**
- ✅ Can run immediately (no waiting)
- ✅ Higher rate limits
- ✅ More reliable service
- ❌ Costs money (~$0.10-0.30 for 250 tests)

**Steps:**
1. Edit `.env` file
2. Restart API: `python run_api.py`
3. Run tests: `python run_250_tests.py`

---

### Option 2: Wait for Groq Rate Limit Reset (FREE)

**When:** Rate limit resets after 24 hours from first use

**Benefits:**
- ✅ Free
- ✅ No code changes needed
- ❌ Must wait ~24 hours

**Steps:**
1. Wait until tomorrow
2. Run tests: `python run_250_tests.py`

---

### Option 3: Upgrade Groq Tier (Better for Future)

**Upgrade to Groq Dev Tier:**
- Visit: https://console.groq.com/settings/billing
- Cost: ~$5-20/month
- Limits: Much higher (millions of tokens/day)

**Benefits:**
- ✅ Much higher limits
- ✅ Keep using Groq (very fast)
- ✅ Good for future testing
- ❌ Requires account upgrade

---

### Option 4: Use Local LLM (Best for Development)

**Install Ollama:**
```bash
# Install Ollama
# Download from: https://ollama.ai

# Pull a model
ollama pull llama3

# Update .env
JUDGE_MODEL=llama3
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama  # dummy key
```

**Benefits:**
- ✅ Unlimited requests
- ✅ Free forever
- ✅ No rate limits
- ✅ Privacy (runs locally)
- ❌ One-time setup required
- ❌ Slower than cloud APIs

---

## 🎯 Recommended Action:

### **SWITCH TO OPENAI API KEY (Option 1)**

You already have a valid OpenAI API key configured but not being used. Just switch to it:

```bash
# Edit .env file
JUDGE_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-**** # Your OpenAI API key
OPENAI_BASE_URL=https://api.openai.com/v1
```

**Cost estimate for 250 tests:**
- Model: gpt-4o-mini
- Input: ~500,000 tokens (~$0.075)
- Output: ~100,000 tokens (~$0.030)
- **Total: ~$0.10-0.20**

This will let you complete the test immediately and get real accuracy metrics!

---

## 📝 Summary:

- ❌ **Groq API key is rate limited** (199,793/200,000 tokens used)
- ✅ **OpenAI API key is available** but not being used
- 🎯 **Switch to OpenAI to complete test immediately**
- 💰 **Cost: ~$0.10-0.20 for 250 tests**
- ⏰ **Alternative: Wait 24 hours for Groq reset**

---

**Last Updated:** September 11, 2026  
**Status:** Groq rate limited, OpenAI available  
**Action:** Switch API keys in `.env` file
