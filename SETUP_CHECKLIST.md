# Setup Checklist

## ✅ Pre-requisites

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] npm installed
- [ ] OpenAI API key (get from https://platform.openai.com/api-keys)

---

## 🔧 Backend Setup

### Step 1: Navigate to backend
```bash
cd backend
```

### Step 2: Create virtual environment
```bash
python -m venv .venv
```

### Step 3: Activate virtual environment
```bash
# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Create .env file
```bash
# Create .env file in backend directory
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key-here
DATABASE_URL=sqlite+aiosqlite:///./data/cox_automotive.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
EOF
```

**⚠️ IMPORTANT:** Replace `your-openai-api-key-here` with your actual OpenAI API key!

### Step 6: Run backend
```bash
python main.py
```

**Expected output:**
```
🚀 Starting Cox Automotive AI Analytics Agent...
✓ Database initialized
📊 Seeding demo data...
✓ Demo data seeded successfully
✓ Session storage ready at data/sessions
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Verify backend is running
- Open browser: http://localhost:8000
- Should see: `{"name":"Cox Automotive AI Analytics Agent","version":"1.0.0","status":"running","docs":"/docs"}`
- API docs: http://localhost:8000/docs

**✅ Backend Setup Complete!**

---

## 🎨 Frontend Setup

### Step 1: Navigate to frontend
```bash
# Note: folder is named "fontend" (typo), not "frontend"
cd fontend
```

### Step 2: Install dependencies
```bash
npm install
```

### Step 3: Run frontend
```bash
npm run dev
```

**Expected output:**
```
  ▲ Next.js 14.0.4
  - Local:        http://localhost:3000
  - ready started server on 0.0.0.0:3000
```

### Step 4: Verify frontend is running
- Open browser: http://localhost:3000
- Should see the AI Data Analytics interface

**✅ Frontend Setup Complete!**

---

## 🧪 Testing the Setup

### Test 1: Backend Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status":"healthy"}`

### Test 2: Backend API
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me F&I revenue trends"}'
```
**Expected:** JSON response with analysis

### Test 3: Frontend-Backend Connection
1. Open http://localhost:3000
2. Type a question in the chat: "Why did F&I revenue drop?"
3. Should receive AI response with data

### Test 4: Demo Scenarios
1. Click a demo scenario button (e.g., "F&I Revenue Drop")
2. Should see detailed analysis

---

## 🐛 Common Issues & Solutions

### Issue: "Module not found" errors in backend
**Solution:**
```bash
cd backend
source .venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

### Issue: "OPENAI_API_KEY not found"
**Solution:**
- Check `.env` file exists in `backend/` directory
- Verify API key is correct (starts with `sk-`)
- Restart backend after creating/editing `.env`

### Issue: Frontend can't connect to backend
**Solution:**
- Verify backend is running on port 8000
- Check browser console for CORS errors
- Verify `CORS_ORIGINS` in backend `.env` includes `http://localhost:3000`

### Issue: Database errors
**Solution:**
```bash
cd backend
rm -rf data/cox_automotive.db  # Delete database
python main.py  # Will recreate and seed data
```

### Issue: npm install fails
**Solution:**
```bash
cd fontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Port already in use
**Solution:**
- Backend (8000): Change `API_PORT` in `.env` or kill process using port 8000
- Frontend (3000): Kill process or use `npm run dev -- -p 3001`

---

## 📋 Verification Checklist

After setup, verify:

- [ ] Backend runs without errors
- [ ] Backend responds to `/health` endpoint
- [ ] Frontend runs without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Chat interface appears
- [ ] Can send a message and receive response
- [ ] Demo scenarios work
- [ ] Database exists at `backend/data/cox_automotive.db`
- [ ] No errors in browser console
- [ ] No errors in backend terminal

---

## 🚀 Quick Start Commands

### Start Everything (in separate terminals):

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd fontend
npm run dev
```

Then open: http://localhost:3000

---

## 📝 Next Steps After Setup

1. ✅ Try demo scenarios
2. ✅ Explore different dashboards (sidebar navigation)
3. ✅ Ask custom questions in chat
4. ✅ Check API documentation at http://localhost:8000/docs
5. ✅ Review PROJECT_OVERVIEW.md for architecture details

---

## 💡 Tips

- Keep backend terminal open to see logs
- Check browser console (F12) for frontend errors
- Backend auto-reloads on code changes (if DEBUG=True)
- Frontend hot-reloads automatically
- Database auto-seeds on first run
- Sessions are stored in `backend/data/sessions/`

---

**Happy coding! 🎉**

