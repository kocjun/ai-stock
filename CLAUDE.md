# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered stock analysis platform for Korean stock markets (KOSPI/KOSDAQ), combining multi-agent AI orchestration with paper trading capabilities.

**Tech Stack:**
- **CrewAI**: Multi-agent orchestration framework for analysis workflows
- **Ollama**: Local LLM inference (default: llama3.1:8b or gpt-oss:120b)
- **PostgreSQL**: Data storage with financial metrics and trading history
- **FinanceDataReader**: Korean stock data collection
- **Dash/Plotly**: Real-time web dashboard for paper trading
- **n8n**: Workflow automation platform

**Project Status:** Phase 1-4 Complete (AI analysis system + paper trading + dashboard)

## Architecture

### Core Components

**1. AI Agent System (`core/`)**
- **agents/**: 8 specialized AI agents for different analysis tasks
  - `investment_crew.py`: Data Curator (data collection & quality)
  - `screening_crew.py`: Screening Analyst (factor-based filtering)
  - `risk_crew.py`: Risk Manager (volatility, MDD, VaR analysis)
  - `portfolio_crew.py`: Portfolio Planner (optimization & rebalancing)
  - `alert_manager.py`: Alert Manager (price monitoring)
  - `integrated_crew.py`: Orchestrates all agents for comprehensive analysis
  - `market_news_crew.py`: News aggregation and sentiment analysis
  - `kospi_etf_analyzer.py`: ETF analysis

- **modules/**: Standalone analysis modules (can be used independently)
  - `factor_scoring.py`: Multi-factor stock scoring (value/growth/momentum/quality/stability)
  - `financial_metrics.py`: Financial ratio calculations (PER, PBR, ROE, etc.)
  - `risk_analysis.py`: Risk metrics (volatility, Sharpe ratio, MDD, VaR)
  - `portfolio_optimization.py`: Asset allocation strategies (equal-weight, risk-parity, etc.)
  - `backtesting.py`: Historical performance simulation with 9 metrics
  - `technical_indicators.py`: Technical analysis (RSI, MACD, Bollinger Bands)
  - `volume_analysis.py`: Trading volume patterns
  - `sector_leader_detector.py`: Sector rotation and leadership analysis

- **tools/**: CrewAI custom tools (agent-callable functions)
  - `data_collection_tool.py`: FinanceDataReader integration
  - `data_quality_tool.py`: Data validation and coverage checks
  - `financial_analysis_tool.py`: Financial metrics calculation
  - `technical_analysis_tool.py`: Technical indicator analysis
  - `risk_analysis_tool.py`: Portfolio risk assessment
  - `portfolio_tool.py`: Portfolio construction and optimization
  - `backtesting_tool.py`: Strategy backtesting
  - `alert_tool.py`: Price alert monitoring
  - `n8n_webhook_tool.py`: n8n workflow integration

- **utils/**: Shared utilities
  - `db_utils.py`: PostgreSQL connection management
  - `llm_utils.py`: LLM client initialization with auto-fallback
  - `collect_data.py`: Direct data collection without agents
  - `email_sender.py`: Email notification system
  - `market_news_sender.py`: Market news email delivery
  - `news_fetcher.py`: News scraping and aggregation
  - `market_metrics.py`: Market-wide metrics calculation
  - `exclusion_manager.py`: Stock exclusion list management

**2. Paper Trading System (`paper_trading/`)**
- `paper_trading.py`: Virtual account trading execution (buy/sell with commission simulation)
- `portfolio_manager.py`: Position management, stop-loss/take-profit automation
- `trading_crew.py`: AI-driven automated trading using CrewAI agents
- `performance_reporter.py`: Performance analytics and reporting
- `dashboard.py`: Real-time Dash/Plotly web dashboard
- `dashboard_data.py`: Dashboard data provider
- `price_updater.py`: Real-time price update service
- `price_scheduler.py`: Scheduled price data collection
- `sector_leader_strategy.py`: Sector rotation strategy implementation
- `ai_sector_leader_strategy.py`: AI-enhanced sector strategy
- `leader_strategy.py`: Leadership-based stock selection
- `ai_analysis_storage.py`: Stores AI analysis results for trading decisions
- `redteam_validator.py`: Validates trading decisions against constraints
- `setup_schema.py`: Database schema initialization for paper trading
- `manage_exclusions.py`: Interactive exclusion list management

**3. Database Schema**

Key tables:
- `stocks`: Stock master data (code, name, market, sector)
- `prices`: Daily OHLCV price data
- `financials`: Quarterly financial statements
- `news_summary`: News articles with sentiment scores
- `data_collection_logs`: Data collection audit trail
- `virtual_accounts`: Paper trading account balances
- `positions`: Current stock holdings
- `trades`: Trade execution history
- `portfolio_snapshots`: Daily portfolio state snapshots
- `stock_exclusions`: Excluded stocks list
- `ai_stock_analyses`: AI analysis results storage

Views:
- `latest_financials`: Most recent financial data with calculated ratios
- `stocks_with_latest_price`: Stock info joined with latest price

**4. LLM Integration Pattern**

The system uses `build_llm()` from `core/utils/llm_utils.py`:
- **Default mode**: Ollama local LLM (free, configured via `OPENAI_API_BASE`)
- **Redteam mode**: OpenAI API (for validation, set `LLM_MODE=redteam`)
- **Auto-fallback**: If primary model unavailable, falls back to `OPENAI_MODEL_FALLBACK`
- **Health check**: Verifies model availability before agent execution

**5. Data Collection Strategy**

`investment_crew.py` uses intelligent collection profiles:
- **Monday/Thursday**: Large-cap focus (top 70 KOSPI stocks, 30 days)
- **Tuesday/Friday**: Tech/growth stocks (top 80 KOSDAQ stocks, 25 days)
- **Wednesday**: Short-term volatility monitoring (40 stocks, 15 days)
- **Weekend**: Data refresh (50 stocks, 45 days)
- **Auto-bootstrap**: If coverage is low or data is stale, runs full collection

## Development Commands

### Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start Docker services (PostgreSQL + n8n)
cd docker
docker-compose up -d

# Verify services
docker ps
docker-compose logs -f
```

### Running AI Agents

```bash
source .venv/bin/activate

# Individual agents
python core/agents/investment_crew.py      # Data collection
python core/agents/screening_crew.py       # Stock screening
python core/agents/risk_crew.py            # Risk analysis
python core/agents/portfolio_crew.py       # Portfolio optimization
python core/agents/alert_manager.py        # Price alerts
python core/agents/integrated_crew.py      # Full analysis pipeline

# Direct data collection (no agents)
python core/utils/collect_data.py
```

### Paper Trading

```bash
source .venv/bin/activate
cd paper_trading

# Run manual trades
python paper_trading.py

# Run AI-driven trading
python trading_crew.py

# Start real-time dashboard (http://localhost:8050)
./run_dashboard.sh

# Generate performance report
python performance_reporter.py

# Manage stock exclusions
python manage_exclusions.py
```

### Testing

```bash
source .venv/bin/activate

# Unit tests
python tests/test_fdr.py              # FinanceDataReader integration
python tests/test_tools.py            # CrewAI tools
python tests/test_phase2.py           # Analysis modules
python tests/test_phase3.py           # Integrated workflows
python tests/test_backtesting.py      # Backtesting engine

# Integration test (full E2E)
./tests/run_integration_test.sh

# Container-based testing
./scripts/run_tests_in_container.sh
```

### Automation Scripts

```bash
# Set up cron jobs (daily/weekly analysis)
./scripts/setup_cron.sh

# Add alert monitoring cron
./scripts/add_alert_cron.sh

# Manual execution
./scripts/run_daily_collection.sh     # Daily data collection
./scripts/run_weekly_analysis.sh      # Weekly comprehensive analysis
./scripts/run_alerts.sh               # Alert checks
./scripts/send_market_news.sh         # Market news email

# Bootstrap data (stocks + prices + virtual account)
python scripts/bootstrap_data.py
```

### Docker Container Operations

```bash
cd docker

# Build and start all services
docker-compose up -d

# Access Python app container
docker-compose exec ai-stock-app bash

# Run scripts in container
docker-compose --env-file ../.env exec ai-stock-app \
  python core/agents/integrated_crew.py

# View logs
docker-compose logs -f postgres
docker-compose logs -f n8n
docker-compose logs -f ai-stock-app

# Restart services
docker-compose restart

# Stop and remove (WARNING: destroys data if volumes not persisted)
docker-compose down -v
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it investment_postgres psql -U invest_user -d investment_db

# Check data status
SELECT COUNT(*) FROM stocks;
SELECT COUNT(*) FROM prices;
SELECT COUNT(*) FROM trades;
SELECT MAX(date) FROM prices;

# Test connection from Python
python core/utils/db_utils.py
```

### Troubleshooting

```bash
# Check Ollama service
curl http://localhost:11434/api/tags
ollama list
ollama ps

# Check LLM configuration
python core/utils/llm_utils.py

# Check Docker services
docker ps
docker-compose ps

# View recent logs
tail -f logs/cron_daily.log
tail -f logs/cron_alerts.log
tail -f paper_trading/dashboard.log

# Verify environment variables
cat .env | grep -E "DB_|OPENAI_|LLM_"
```

## Key Patterns

### Agent Initialization Pattern

```python
from crewai import Agent, Crew, Process, Task
from core.utils.llm_utils import build_llm
from core.tools.data_collection_tool import DataCollectionTool

# Initialize LLM (auto-selects Ollama or fallback)
llm = build_llm()

# Create agent with tools
agent = Agent(
    role="Data Curator",
    goal="Collect and validate market data",
    backstory="Financial data engineer...",
    tools=[DataCollectionTool()],
    llm=llm,
    verbose=True
)

# Define tasks
task = Task(
    description="Collect KOSPI top 50 stocks, last 30 days",
    agent=agent,
    expected_output="Collection report with quality metrics"
)

# Execute crew
crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential
)
result = crew.kickoff()
```

### Database Access Pattern

```python
from core.utils.db_utils import get_db_connection

# Context manager for safe connection handling
with get_db_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT code, name FROM stocks LIMIT 10")
    stocks = cur.fetchall()
    # Connection auto-closes
```

### Paper Trading Execution Pattern

```python
from paper_trading.paper_trading import execute_buy, execute_sell, get_latest_price

# Get current price
price = get_latest_price("005930")  # Samsung Electronics

# Execute buy order
result = execute_buy(
    account_id=1,
    code="005930",
    price=price,
    shares=10
)

# Execute sell order
result = execute_sell(
    account_id=1,
    code="005930",
    price=price,
    shares=5
)
```

### Custom Tool Pattern

```python
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    argument: str = Field(..., description="Tool argument description")

class MyCustomTool(BaseTool):
    name: str = "my_tool"
    description: str = "Tool description for LLM to understand usage"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, argument: str) -> str:
        try:
            # Implementation
            result = process(argument)
            return f"Success: {result}"
        except Exception as e:
            return f"Error: {str(e)}"
```

## Important Considerations

### Development Principles
- All agent prompts and outputs default to **Korean language**
- Do not delete `.crewai/` directory during active workflows (contains task state)
- System is designed for **defensive analysis only** - do not implement order execution without approval workflows
- All outputs are **reference information only**, never investment advice
- Include disclaimers in all reports

### Data Management
- Data is for **personal analysis only** (no redistribution)
- Use only official APIs (FinanceDataReader, DART OpenAPI)
- Always cite data sources
- Respect rate limits and API terms of service

### LLM Configuration
- Default: Ollama local LLM at `OPENAI_API_BASE` (usually `http://127.0.0.1:11434`)
- For remote LLM servers (e.g., NAS): Set `OPENAI_API_BASE=http://192.168.x.x:11434`
- Primary model: `OPENAI_MODEL_NAME` (default: gpt-oss:120b or llama3.1:8b)
- Fallback model: `OPENAI_MODEL_FALLBACK` (used if primary unavailable)
- Validation mode: Set `LLM_MODE=redteam` to use OpenAI API instead

### Paper Trading
- Commission rate: 0.015% per trade (Korean brokerage average)
- Virtual accounts start with configurable initial balance
- Stop-loss and take-profit are automated via `portfolio_manager.py`
- Dashboard runs on port 8050 by default
- All trades are logged to `trades` table for audit trail

### Docker Network
- PostgreSQL and n8n communicate via `investment_network`
- Container names: `investment_postgres`, `n8n`, `ai_stock_app`
- Data persists in volumes: `postgres-data/`, `n8n-data/`
- PostgreSQL exposed on host port 15432 (maps to container 5432)
- n8n exposed on host port 5678

### Cron Automation
- Daily 18:00: Data collection (`run_daily_collection.sh`)
- Weekdays 08:30, 16:00: Alert checks (`run_alerts.sh`)
- Saturday 09:00: Weekly comprehensive analysis (`run_weekly_analysis.sh`)
- Check with: `crontab -l`

## Common Issues

**Ollama connection refused**
```bash
# Start Ollama server
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

**Model not found**
```bash
# Download required model
ollama pull llama3.1:8b
ollama list
```

**PostgreSQL authentication failed**
```bash
# Verify .env settings
cat .env | grep DB_PASSWORD

# Test connection
docker exec -it investment_postgres psql -U invest_user -d investment_db
```

**n8n webhook failure**
```bash
# Restart n8n
cd docker
docker-compose restart n8n

# Test webhook manually
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"test","message":"hello"}'
```

**Dashboard not accessible**
```bash
# Check if process is running
ps aux | grep dashboard

# Kill existing process
./paper_trading/run_dashboard.sh stop

# Restart
./paper_trading/run_dashboard.sh start
```

## Environment Variables Reference

Required variables in `.env`:

```bash
# LLM Configuration
OPENAI_API_BASE=http://127.0.0.1:11434    # Ollama endpoint
OPENAI_MODEL_NAME=gpt-oss:120b            # Primary model
OPENAI_MODEL_FALLBACK=llama3.1:8b         # Fallback model
OPENAI_API_KEY=ollama                      # "ollama" for local, real key for OpenAI
CREWAI_LLM_PROVIDER=ollama                 # LLM provider
LLM_MODE=main                              # "main" (Ollama) or "redteam" (OpenAI)

# Database
DB_HOST=localhost
DB_PORT=15432
DB_NAME=investment_db
DB_USER=invest_user
DB_PASSWORD=<your-password>

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook/crew-webhook
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<your-password>
N8N_DB_USER=invest_user
N8N_DB_PASSWORD=<your-password>
N8N_DB_NAME=n8n_db

# Email (for alerts)
EMAIL_FROM_ADDRESS=<your-email>
REPORT_EMAIL_RECIPIENT=<recipient-email>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# CrewAI
CREWAI_STORAGE_DIR=.crewai/
```

---

**Last Updated:** 2025-12-21
**Version:** 5.0 (Analysis + Paper Trading + Dashboard Complete)
