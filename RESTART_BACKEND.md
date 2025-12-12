# ⚠️ Backend Restart Required

## Current Status

✅ **Configuration Updated:**
- Model set to: `mistralai/mistral-7b-instruct:free`
- `.env` file updated
- `config.py` default updated

⚠️ **Backend needs restart** to load new configuration.

## 🔄 How to Restart Backend

### Option 1: If running with `python main.py`
```bash
# Stop current process (Ctrl+C in the terminal where it's running)
# Or find and kill the process:
ps aux | grep "python main.py" | grep -v grep
kill <PID>

# Restart:
cd backend
source .venv/bin/activate
python main.py
```

### Option 2: If running with `uvicorn`
```bash
# Stop current process
ps aux | grep uvicorn | grep -v grep
kill <PID>

# Restart:
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ After Restart, Test With:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why did F&I revenue drop across Midwest dealers this week?"}'
```

## 🔍 If Still Getting 404 Errors

The model name might not be available. Try these alternatives:

1. **Remove `:free` suffix** (might still be free or very cheap):
   ```bash
   OPENROUTER_MODEL=mistralai/mistral-7b-instruct
   ```

2. **Try other free models:**
   - `google/gemini-flash-1.5` (very cheap, ~$0.075 per 1M tokens)
   - `anthropic/claude-3-haiku` (cheap, ~$0.25 per 1M tokens)

3. **Check OpenRouter dashboard:**
   - Visit: https://openrouter.ai/models
   - Filter by "Tools" capability
   - Look for available free models

## 📝 Current Configuration

**File:** `backend/.env`
```
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

**File:** `backend/app/core/config.py`
```python
openrouter_model: str = "mistralai/mistral-7b-instruct:free"
```

