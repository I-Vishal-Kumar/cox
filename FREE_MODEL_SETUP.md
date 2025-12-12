# Free Model Setup Guide

## ✅ Updated Configuration

I've updated the configuration to use a free model that supports function calling:

**Current Model:** `mistralai/mistral-small-3.2-24b-instruct:free`

## 🔄 Backend Restart Required

**IMPORTANT:** The backend server needs to be restarted to pick up the new `.env` configuration.

### To Restart Backend:

1. **Stop the current backend server** (if running):
   ```bash
   # Find the process
   ps aux | grep uvicorn
   
   # Kill it
   kill <PID>
   ```

2. **Restart the backend:**
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📋 Alternative Free Models to Try

If `mistralai/mistral-small-3.2-24b-instruct:free` doesn't work, try these:

1. **`mistralai/mistral-7b-instruct:free`** - Mistral 7B (mentioned by user)
2. **`deepseek/deepseek-r1-0528:free`** - DeepSeek R1 (if available)
3. **`google/gemini-flash-1.5`** - Very cheap (not free but very low cost)
4. **`anthropic/claude-3-haiku`** - Cheap option (not free but low cost)

## 🔍 How to Check Model Availability

You can check which models support function calling on OpenRouter:
1. Visit: https://openrouter.ai/models
2. Filter by "Tools" capability
3. Look for models with `:free` suffix

## ⚠️ Known Issues

- Some free models may not support function calling even if they claim to
- The `:free` suffix might cause issues with certain models
- Rate limits apply to free models (usually 50-1000 requests/day)

## ✅ Testing After Restart

After restarting the backend, test with:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why did F&I revenue drop across Midwest dealers this week?"}'
```

If you still get 404 errors, try:
1. Remove `:free` suffix and use a very cheap model instead
2. Check OpenRouter dashboard for model availability
3. Verify the model name is exactly correct

