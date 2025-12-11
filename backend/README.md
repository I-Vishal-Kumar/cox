# Cox Automotive AI Analytics Backend

## Overview

The Cox Automotive AI Analytics Backend is a FastAPI-based application that provides AI-powered data analytics for the automotive industry. It features a multi-agent architecture that processes natural language queries and returns intelligent insights, SQL queries, and data visualizations.

## Architecture

### Core Components

- **FastAPI Application** (`main.py`) - Main web server with CORS and lifecycle management
- **Multi-Agent System** (`app/agents/`) - Specialized AI agents for different analytics domains
- **Database Layer** (`app/db/`) - SQLAlchemy models and database management
- **API Routes** (`app/api/`) - RESTful endpoints for frontend integration
- **Analytics Services** (`app/services/`) - Business logic for data processing

### Agent Architecture

The system uses a sophisticated multi-agent approach:

1. **Orchestrator Agent** - Routes queries to appropriate specialized agents
2. **Query Classifier** - Categorizes incoming queries by domain
3. **SQL Agent** - Generates SQL queries from natural language
4. **KPI Agent** - Provides analysis and insights
5. **Root Cause Analyzer** - Performs deep-dive analysis for specific scenarios

## Features

### 🤖 AI-Powered Analytics
- Natural language query processing
- Automatic SQL generation
- Intelligent data analysis and insights
- Root cause analysis for business problems

### 📊 Domain-Specific Analysis
- **F&I Analysis**: Finance & Insurance revenue, penetration rates
- **Logistics Analysis**: Shipment delays, carrier performance
- **Plant Analysis**: Manufacturing downtime, production issues
- **Marketing Analysis**: Campaign performance, ROI tracking
- **KPI Monitoring**: Real-time metrics and alerting

### 🔄 Real-time Processing
- Streaming responses for long queries
- Conversation context management
- Real-time KPI monitoring and alerts

## Installation

### Prerequisites
- Python 3.8+
- SQLite (included)
- OpenAI API key

### Setup

1. **Clone and navigate to backend directory**
```bash
cd co/backend
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file:
```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/cox_automotive.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3002", "http://localhost:5173"]
```

5. **Run the application**
```bash
python main.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Core Chat Interface
- `POST /api/v1/chat` - Process natural language queries
- `GET /api/v1/chat/stream` - Stream responses for long queries

### Dashboard Data
- `GET /api/v1/dashboard/invite` - Marketing (Invite) dashboard data
- `GET /api/v1/dashboard/fni` - F&I analysis dashboard
- `GET /api/v1/dashboard/logistics` - Logistics dashboard
- `GET /api/v1/dashboard/plant` - Plant downtime dashboard

### KPI & Monitoring
- `GET /api/v1/kpi/metrics` - KPI metrics with filtering
- `GET /api/v1/kpi/alerts` - Current KPI alerts

### Data Catalog
- `GET /api/v1/data-catalog/tables` - Available tables and schemas
- `GET /api/v1/demo/scenarios` - Pre-built demo scenarios

### Health & Status
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API information

## Database Schema

### Core Tables

#### Dealers
- Dealer information, regions, locations
- Relationships to all transaction tables

#### FNI Transactions
- Finance & Insurance transaction records
- Revenue tracking, penetration rates
- Finance manager performance

#### Shipments
- Logistics and delivery tracking
- Carrier performance, delay analysis
- Route optimization data

#### Plant Operations
- Manufacturing plant information
- Downtime events and root causes
- Production capacity tracking

#### Marketing Campaigns
- Campaign performance metrics
- Email marketing (Invite) data
- ROI and conversion tracking

#### KPI Metrics
- Daily metric values and targets
- Variance tracking and alerting
- Multi-dimensional analysis

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI functionality | Required |
| `DATABASE_URL` | SQLite database connection string | `sqlite+aiosqlite:///./data/cox_automotive.db` |
| `API_HOST` | Server host address | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `True` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` |

### AI Model Configuration

The system uses OpenAI's GPT-4 model by default. You can configure:
- Model selection in `app/core/config.py`
- Temperature and other parameters in agent initialization
- Custom system prompts for specialized agents

## Development

### Project Structure
```
co/backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── data/                  # SQLite database storage
└── app/
    ├── __init__.py
    ├── agents/            # AI agent implementations
    │   ├── orchestrator.py    # Main orchestrator
    │   ├── sql_agent.py       # SQL generation
    │   ├── kpi_agent.py       # KPI analysis
    │   └── base_agent.py      # Base agent class
    ├── api/               # API routes
    │   └── routes.py          # All API endpoints
    ├── core/              # Core configuration
    │   └── config.py          # Settings management
    ├── db/                # Database layer
    │   ├── database.py        # Database connection
    │   ├── models.py          # SQLAlchemy models
    │   └── seed_data.py       # Demo data seeding
    ├── models/            # Pydantic schemas
    │   └── schemas.py         # API request/response models
    ├── services/          # Business logic
    │   └── analytics_service.py
    └── utils/             # Utility functions
```

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `get_system_prompt()` and `process()` methods
3. Register agent in orchestrator
4. Add routing logic in query classifier

### Database Migrations

The application automatically:
- Creates database on first run
- Seeds demo data if database is empty
- Handles schema updates through SQLAlchemy

### Testing

```bash
# Run with demo data
python main.py

# Test API endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show F&I revenue trends"}'
```

## Demo Scenarios

The system includes pre-built demo scenarios:

1. **F&I Revenue Drop** - Analyzes revenue decline in Midwest region
2. **Logistics Delays** - Identifies carrier and route issues
3. **Plant Downtime** - Root cause analysis for production issues

## Monitoring & Logging

- Health check endpoint for uptime monitoring
- Automatic session cleanup and memory management
- Error handling with graceful degradation
- Conversation history tracking

## Security Considerations

- API key management through environment variables
- CORS configuration for frontend integration
- Input validation through Pydantic models
- SQL injection prevention through parameterized queries

## Performance Optimization

- Async/await for database operations
- Connection pooling with SQLAlchemy
- Streaming responses for large datasets
- Conversation context management

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key in `.env` file
   - Check API rate limits and billing

2. **Database Issues**
   - Ensure `data/` directory is writable
   - Check SQLite file permissions

3. **CORS Errors**
   - Update `CORS_ORIGINS` in `.env`
   - Verify frontend URL matches allowed origins

4. **Import Errors**
   - Ensure virtual environment is activated
   - Install all requirements: `pip install -r requirements.txt`

### Debug Mode

Enable debug mode in `.env`:
```env
DEBUG=True
```

This provides:
- Detailed error messages
- Auto-reload on code changes
- Enhanced logging

## Deployment

### Production Considerations

1. **Environment Variables**
   - Use production OpenAI API key
   - Set `DEBUG=False`
   - Configure appropriate CORS origins

2. **Database**
   - Consider PostgreSQL for production
   - Implement proper backup strategy
   - Set up connection pooling

3. **Security**
   - Use HTTPS in production
   - Implement rate limiting
   - Add authentication/authorization

4. **Monitoring**
   - Set up health check monitoring
   - Implement logging aggregation
   - Monitor API usage and costs

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints for all functions
3. Include docstrings for public methods
4. Test new features with demo scenarios
5. Update API documentation for new endpoints

## License

Internal Cox Automotive project - All rights reserved.