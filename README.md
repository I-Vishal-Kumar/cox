# Cox Automotive AI Data Analytics Agent

An AI-powered data analytics platform for Cox Automotive that enables natural language queries, automated KPI monitoring, and root cause analysis.

## Architecture

```
cox/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── agents/          # LangChain AI Agents
│   │   │   ├── base_agent.py
│   │   │   ├── sql_agent.py      # NL to SQL conversion
│   │   │   ├── kpi_agent.py      # KPI analysis & RCA
│   │   │   └── orchestrator.py   # Multi-agent orchestration
│   │   ├── api/             # API Routes
│   │   ├── core/            # Configuration
│   │   ├── db/              # Database models & seed data
│   │   ├── models/          # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── data/                # SQLite database
│   └── main.py              # FastAPI application
│
└── frontend/                # Next.js Frontend
    └── src/
        ├── app/             # Next.js pages (App Router)
        │   ├── page.tsx           # AI Chat interface
        │   ├── invite/            # Marketing dashboard
        │   ├── alerts/            # KPI alerts
        │   ├── catalog/           # Data catalog
        │   └── analysis/          # Analysis dashboards
        ├── components/      # React components
        │   ├── chat/              # Chat interface
        │   ├── dashboard/         # Dashboard components
        │   └── ui/                # Reusable UI components
        ├── lib/             # API client
        └── types/           # TypeScript types
```

## Features

### 1. Conversational Business Intelligence
- Natural language to SQL conversion
- Auto-generated charts and visualizations
- Follow-up questions and drill-downs
- Data quality warnings

### 2. Automated KPI Monitoring
- Real-time KPI tracking
- Anomaly detection with ML
- Root cause analysis
- Proactive alerts

### 3. Demo Scenarios
Three pre-built scenarios with realistic data:

1. **F&I Revenue Drop** - "Why did F&I revenue drop across Midwest dealers this week?"
2. **Logistics Delays** - "Who delayed — carrier, route, or weather?"
3. **Plant Downtime** - "Which plants showed downtime and why?"

## Tech Stack

### Backend
- **FastAPI** - High-performance async Python web framework
- **LangChain** - AI agent orchestration
- **OpenAI GPT-4** - Natural language understanding
- **SQLAlchemy** - Async ORM
- **SQLite** - Demo database (can swap to BigQuery)

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Heroicons** - Icons

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the server (auto-seeds demo data on first run)
python main.py
```

The backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

### Chat
- `POST /api/v1/chat` - Send a message to the AI analyst
- `GET /api/v1/chat/stream` - Stream a response

### Dashboards
- `GET /api/v1/dashboard/invite` - Invite (Marketing) dashboard data
- `GET /api/v1/dashboard/fni` - F&I analysis data
- `GET /api/v1/dashboard/logistics` - Logistics data
- `GET /api/v1/dashboard/plant` - Plant downtime data

### KPIs
- `GET /api/v1/kpi/metrics` - Get KPI metrics
- `GET /api/v1/kpi/alerts` - Get KPI alerts

### Data Catalog
- `GET /api/v1/data-catalog/tables` - Get available tables

### Demo
- `GET /api/v1/demo/scenarios` - Get demo scenarios

## Demo Data

The system auto-generates realistic demo data with cause-and-effect relationships:

### Dealers (12)
- 5 Midwest dealers (3 with F&I issues)
- 3 Northeast dealers
- 2 Southeast dealers
- 2 West dealers

### F&I Transactions (~2,000)
- 4 weeks of data
- Clear week-over-week drop in Midwest
- Finance manager-level attribution

### Shipments (~400)
- 2 weeks of data
- 18% delay rate in recent week
- Carrier X delays on specific routes
- Dwell time increase from 1.2 to 3.1 hours

### Plant Downtime (~20 events)
- Plant A: 6.5 hours (paint defects, conveyor)
- Plant B: 4.2 hours (Supplier Q shortage)
- Plant C: 2.3 hours (maintenance overrun)

### Marketing Campaigns (~1,000)
- 20 campaign types
- 6 months of data
- Realistic open rates and revenue

## Xtime Dashboards (PDF Reference)

The UI is designed to match the Xtime Technology Suite:

1. **Schedule** - Appointment management
2. **Engage** - Customer experience management
3. **Inspect** - Vehicle inspection software
4. **Invite** - Marketing software (implemented first)

## Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cox_automotive.db

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build
npm start
```

## License

Confidential - QSourceGroup Inc.
