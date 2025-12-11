# Cox Automotive AI Analytics - Project Overview

## 🏗️ Architecture Summary

This is a **full-stack AI-powered data analytics platform** for Cox Automotive with:

- **Backend**: FastAPI (Python) with LangChain AI agents
- **Frontend**: Next.js 14 (TypeScript/React) with Tailwind CSS
- **Database**: SQLite (with demo data)
- **AI**: OpenAI GPT-4 via LangChain for natural language processing

---

## 📁 Project Structure

```
co/
├── backend/              # Python FastAPI backend
│   ├── main.py          # FastAPI app entry point
│   ├── requirements.txt # Python dependencies
│   └── app/
│       ├── agents/      # AI agents (orchestrator, SQL, KPI)
│       ├── api/         # API routes
│       ├── db/          # Database models & seed data
│       ├── services/    # Business logic
│       └── core/        # Configuration
│
└── fontend/             # Next.js frontend (note: typo in folder name)
    ├── package.json     # Node.js dependencies
    └── src/
        ├── app/         # Next.js pages (App Router)
        ├── components/  # React components
        ├── lib/         # API client functions
        └── types/       # TypeScript types
```

---

## 🔄 How It Works - Data Flow

### 1. **User Query Flow**

```
User Types Question
    ↓
Frontend: ChatInterface.tsx
    ↓
POST /api/v1/chat
    ↓
Backend: routes.py → chat()
    ↓
LangChainAnalyticsOrchestrator.process_query()
    ↓
AI Agent System:
  - Classifies query type
  - Routes to appropriate agent (SQL, KPI, etc.)
  - Generates SQL queries
  - Executes queries on database
  - Analyzes results
  - Generates insights & charts
    ↓
Returns: {
  message: "Analysis text",
  sql_query: "SELECT...",
  data: [...],
  chart_config: {...},
  recommendations: [...]
}
    ↓
Frontend displays: Message + Chart + Data Table
```

### 2. **Backend Architecture**

#### **Main Components:**

1. **FastAPI Application** (`main.py`)
   - Starts on `http://localhost:8000`
   - Auto-initializes database on startup
   - Auto-seeds demo data if database is empty
   - CORS enabled for frontend

2. **AI Orchestrator** (`app/agents/langchain_orchestrator.py`)
   - Uses LangChain's `create_agent` with tools
   - Manages conversation history
   - Routes queries to specialized agents:
     - **SQL Agent**: Converts natural language → SQL
     - **KPI Agent**: Analyzes metrics and alerts
     - **Dashboard Tools**: Domain-specific analysis

3. **Database Layer** (`app/db/`)
   - SQLAlchemy async ORM
   - Models: Dealers, FNI Transactions, Shipments, Plant Downtime, Marketing Campaigns, KPI Metrics
   - Auto-seeds realistic demo data

4. **API Routes** (`app/api/routes.py`)
   - `POST /api/v1/chat` - Main chat endpoint
   - `GET /api/v1/chat/stream` - Streaming responses
   - `GET /api/v1/dashboard/*` - Dashboard data endpoints
   - `GET /api/v1/kpi/*` - KPI metrics and alerts
   - `GET /api/v1/data-catalog/tables` - Available tables

### 3. **Frontend Architecture**

#### **Main Components:**

1. **Chat Interface** (`src/components/chat/ChatInterface.tsx`)
   - Main conversational UI
   - Sends messages to backend
   - Displays responses with charts and tables
   - Demo mode fallback if backend is offline

2. **Pages** (`src/app/`)
   - `/` - Main chat interface
   - `/invite` - Marketing dashboard
   - `/analysis/fni` - F&I analysis
   - `/analysis/logistics` - Logistics dashboard
   - `/analysis/plant` - Plant downtime
   - `/alerts` - KPI alerts
   - `/catalog` - Data catalog

3. **API Client** (`src/lib/api.ts`)
   - Functions to call backend endpoints
   - Error handling
   - Response parsing

---

## 🛠️ Setup Instructions

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (required!)
# Add your OpenAI API key:
echo "OPENAI_API_KEY=your-key-here" > .env
echo "DATABASE_URL=sqlite+aiosqlite:///./data/cox_automotive.db" >> .env
echo "API_HOST=0.0.0.0" >> .env
echo "API_PORT=8000" >> .env
echo "DEBUG=True" >> .env

# Run the server
python main.py
```

**Backend will:**
- Start on `http://localhost:8000`
- Create database if it doesn't exist
- Auto-seed demo data on first run
- Provide API docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd fontend  # Note: folder name has typo "fontend" not "frontend"

# Install dependencies
npm install

# Run development server
npm run dev
```

**Frontend will:**
- Start on `http://localhost:3000`
- Connect to backend at `http://localhost:8000`
- Show demo mode if backend is offline

---

## 🎯 Key Features

### 1. **Conversational BI**
- Ask questions in natural language
- AI converts to SQL queries
- Returns data + charts + insights
- Example: "Why did F&I revenue drop in Midwest?"

### 2. **Multi-Agent System**
- **Orchestrator**: Routes queries to right agent
- **SQL Agent**: Generates and executes SQL
- **KPI Agent**: Analyzes metrics and anomalies
- **Dashboard Tools**: Domain-specific analysis

### 3. **Demo Scenarios**
Pre-built scenarios for testing:
- F&I Revenue Drop (Midwest dealers)
- Logistics Delays (carrier analysis)
- Plant Downtime (root cause analysis)

### 4. **Real-time Dashboards**
- Marketing (Invite) dashboard
- F&I analysis dashboard
- Logistics dashboard
- Plant downtime dashboard
- KPI alerts dashboard

---

## 🔌 API Endpoints

### Chat
- `POST /api/v1/chat` - Send message, get analysis
- `GET /api/v1/chat/stream` - Stream response (SSE)

### Dashboards
- `GET /api/v1/dashboard/invite` - Marketing data
- `GET /api/v1/dashboard/fni` - F&I analysis
- `GET /api/v1/dashboard/logistics` - Logistics data
- `GET /api/v1/dashboard/plant` - Plant downtime

### KPIs
- `GET /api/v1/kpi/metrics` - KPI metrics (with filters)
- `GET /api/v1/kpi/alerts` - Current alerts

### Data Catalog
- `GET /api/v1/data-catalog/tables` - Available tables
- `GET /api/v1/demo/scenarios` - Demo scenarios

---

## 📊 Database Schema

### Core Tables:
1. **dealers** - Dealer info (12 dealers, 4 regions)
2. **fni_transactions** - F&I transactions (~2,000 records)
3. **shipments** - Logistics data (~400 records)
4. **plant_downtime** - Manufacturing events (~20 records)
5. **marketing_campaigns** - Campaign data (~1,000 records)
6. **kpi_metrics** - Daily metrics (~3,000 records)

All data is auto-seeded with realistic demo data on first run.

---

## 🔑 Environment Variables

### Backend (.env file)
```env
OPENAI_API_KEY=sk-...          # Required!
DATABASE_URL=sqlite+aiosqlite:///./data/cox_automotive.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend
- Uses hardcoded `http://localhost:8000` in `src/lib/api/config.ts`
- Can be changed to environment variable if needed

---

## 🚀 How to Use

1. **Start Backend:**
   ```bash
   cd backend
   source .venv/bin/activate
   python main.py
   ```

2. **Start Frontend:**
   ```bash
   cd fontend
   npm run dev
   ```

3. **Open Browser:**
   - Go to `http://localhost:3000`
   - Type a question like: "Why did F&I revenue drop in Midwest?"
   - Or click a demo scenario button

4. **View Dashboards:**
   - Use sidebar to navigate to different dashboards
   - Each dashboard shows specialized analytics

---

## 🧪 Testing

### Test Backend:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show F&I revenue trends"}'
```

### Test Frontend:
- Open `http://localhost:3000`
- Try demo scenarios
- Check browser console for errors

---

## 🐛 Troubleshooting

### Backend Issues:
1. **OpenAI API Errors**
   - Check `.env` file has valid `OPENAI_API_KEY`
   - Verify API key has credits

2. **Database Errors**
   - Ensure `data/` directory is writable
   - Delete `data/cox_automotive.db` to reset

3. **Import Errors**
   - Activate virtual environment: `source .venv/bin/activate`
   - Reinstall: `pip install -r requirements.txt`

### Frontend Issues:
1. **API Connection Errors**
   - Verify backend is running on port 8000
   - Check browser console for CORS errors
   - Frontend will show "demo mode" if backend is offline

2. **Build Errors**
   - Clear `.next`: `rm -rf .next`
   - Reinstall: `rm -rf node_modules && npm install`

---

## 📝 Key Files to Understand

### Backend:
- `main.py` - FastAPI app startup
- `app/api/routes.py` - All API endpoints
- `app/agents/langchain_orchestrator.py` - AI orchestrator
- `app/agents/tools.py` - AI agent tools
- `app/db/models.py` - Database models
- `app/db/seed_data.py` - Demo data generation

### Frontend:
- `src/app/page.tsx` - Main chat page
- `src/components/chat/ChatInterface.tsx` - Chat UI
- `src/lib/api.ts` - API client functions
- `src/lib/api/config.ts` - API base URL

---

## 🎓 Learning Path

1. **Start with Backend:**
   - Read `main.py` to understand startup
   - Check `routes.py` for API structure
   - Explore `langchain_orchestrator.py` for AI logic

2. **Then Frontend:**
   - Check `ChatInterface.tsx` for UI
   - See `api.ts` for backend communication
   - Explore dashboard pages

3. **Understand Data Flow:**
   - User query → Frontend → Backend API
   - Backend → AI Agent → SQL → Database
   - Results → Backend → Frontend → Display

---

## 🔮 Next Steps

After setup:
1. ✅ Backend running on port 8000
2. ✅ Frontend running on port 3000
3. ✅ Database seeded with demo data
4. ✅ Try demo scenarios
5. ✅ Explore different dashboards
6. ✅ Ask custom questions

---

## 📚 Additional Resources

- Backend README: `backend/README.md`
- Frontend README: `fontend/README.md`
- Main README: `README.md`
- API Documentation: `http://localhost:8000/docs` (when backend is running)

---

**Note:** The frontend folder is named `fontend` (typo) instead of `frontend`. Keep this in mind when navigating!

