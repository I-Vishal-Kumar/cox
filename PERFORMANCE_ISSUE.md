# ⚠️ Performance Issue - Free Model Too Slow

## Problem

The free model (`mistralai/mistral-7b-instruct:free`) is **taking too long** (>15 seconds) to respond to complex queries with tool calling.

**Test Results:**
- Simple query: ~4.6 seconds ✅
- Complex F&I query: **>15 seconds (timeout)** ❌

## Root Cause

Free models on OpenRouter:
- Have **rate limits** and **slower processing**
- May have **limited function calling support**
- Can be **overloaded** with many users

## ✅ Solutions Applied

1. **Added timeout settings:**
   - 30 second timeout for LLM calls
   - Reduced retries to 1 (faster failure)

2. **Files updated:**
   - `backend/app/agents/langchain_orchestrator.py`
   - `backend/app/agents/base_agent.py`

## 🔧 Recommended Solutions

### Option 1: Use a Faster Cheap Model (Recommended)

Switch to a very cheap but faster model:

```bash
# In backend/.env
OPENROUTER_MODEL=google/gemini-flash-1.5
```

**Cost:** ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens
**Speed:** Much faster than free models
**Function Calling:** ✅ Full support

### Option 2: Use Claude Haiku (Fast & Cheap)

```bash
# In backend/.env
OPENROUTER_MODEL=anthropic/claude-3-haiku
```

**Cost:** ~$0.25 per 1M input tokens
**Speed:** Very fast
**Function Calling:** ✅ Full support

### Option 3: Enable Demo Mode (For Testing)

Bypass LLM entirely for testing:

```bash
# In backend/.env
DEMO_MODE=True
```

This uses pre-built responses without API calls.

### Option 4: Optimize System Prompt

Reduce the system prompt size to speed up processing (already optimized, but can be further reduced).

## 🚀 Quick Fix

**Restart backend after updating .env:**

```bash
cd backend
# Update .env with one of the models above
# Then restart:
python main.py
```

## 📊 Model Comparison

| Model | Cost | Speed | Function Calling | Recommendation |
|-------|------|-------|------------------|----------------|
| `mistralai/mistral-7b-instruct:free` | Free | ❌ Very Slow | ⚠️ Limited | Not recommended |
| `google/gemini-flash-1.5` | Very Cheap | ✅ Fast | ✅ Full | **Best option** |
| `anthropic/claude-3-haiku` | Cheap | ✅ Very Fast | ✅ Full | Good option |
| `openai/gpt-3.5-turbo` | Cheap | ✅ Fast | ✅ Full | Good option |

## ⚡ Immediate Action

**Change to Gemini Flash for best performance:**

```bash
cd backend
sed -i 's|OPENROUTER_MODEL=.*|OPENROUTER_MODEL=google/gemini-flash-1.5|' .env
# Restart backend
```

This will give you:
- ✅ Fast responses (< 5 seconds)
- ✅ Full function calling support
- ✅ Very low cost (~$0.075 per 1M tokens)
- ✅ Reliable performance

