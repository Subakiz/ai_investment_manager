# AlphaGen Personal Investment Platform

AlphaGen is a Phase 1 AI-powered investment platform focused on the Indonesian Stock Exchange (IDX). It collects market data for LQ45 stocks and Indonesian financial news with automated scheduling and provides a REST API for data access.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap, Build, and Test the Repository
- **Check Python version**: `python3 --version` (requires Python 3.11+, found 3.12.3 ✓)
- **Run setup script**: `chmod +x scripts/setup.sh && ./scripts/setup.sh` -- takes 2-3 minutes normally, but may take up to 10 minutes if network is slow. **NEVER CANCEL**. Set timeout to 15+ minutes.
- **Run validation test**: `python test_setup.py` -- takes < 1 second, always run this first
- **Copy environment template**: `cp .env.template .env` (edit with your actual API keys)

### Critical Dependency Installation Issues
- **CRITICAL**: `pip install -r requirements.txt` **WILL FAIL** due to network timeouts in restricted environments
- **This is EXPECTED behavior** - not a broken setup
- **Workaround**: Install minimal dependencies individually: `pip install python-dotenv fastapi uvicorn --timeout 120`
- **Common error**: "HTTPSConnectionPool(host='pypi.org'): Read timed out" - this is normal in sandboxed environments
- **Fallback**: Basic functionality works without full dependencies, API server will show helpful error messages

### Run the Application
- **Start PostgreSQL**: `docker compose up -d db` (modern Docker) or `docker-compose up -d db` (legacy)
- **Check database**: `python -m src.database.database check` (will fail gracefully if DB not available)
- **Initialize data pipeline**: `python -m src.data_pipeline.pipeline init`
- **Start API server**: `python -m src.api.main` (requires fastapi/uvicorn installed)
- **Access API**: http://localhost:8000 (when running)

### Data Collection Commands
- **Manual collection**: `python -m src.data_pipeline.pipeline collect --type all --days 1`
- **Market data only**: `python -m src.data_pipeline.pipeline collect --type market --days 7`
- **News data only**: `python -m src.data_pipeline.pipeline collect --type news --days 1`
- **Health check**: `python -m src.data_pipeline.pipeline health`
- **Via script wrapper**: `./scripts/run_pipeline.sh --type all --days 1`

### Cron Job Setup
- **Setup automation**: `./scripts/setup_cron.sh`
- **View jobs**: `crontab -l`
- **Remove jobs**: `crontab -r`

## Validation Scenarios

**ALWAYS run these commands after making changes to verify the system is functional:**

1. **Basic validation**: `python test_setup.py` (< 1 second)
2. **Configuration test**: `python -c "from src.config.settings import config; print('Config OK')"`
3. **Pipeline test**: `python -m src.data_pipeline.pipeline health`
4. **Docker validation**: `docker compose config` (< 1 second, may show version warning)

**NEVER try to run the full application without dependencies** - it will fail gracefully with helpful messages.

## Timing Expectations and Critical Warnings

- **NEVER CANCEL**: Setup script takes 2-10 minutes depending on network. Set timeout to 15+ minutes.
- **NEVER CANCEL**: `pip install` operations - they may timeout but this doesn't break functionality
- **Basic validation**: `python test_setup.py` takes < 30ms (extremely fast)
- **Pipeline commands**: Take < 1 second (stubs in Phase 1)
- **Docker commands**: `docker compose config` takes < 100ms
- **Configuration access**: Instant (< 10ms)

## Common Issues and Solutions

### Dependency Installation Fails (EXPECTED)
```bash
# This is NORMAL in sandboxed environments
./scripts/setup.sh
# ERROR: HTTPSConnectionPool(host='pypi.org'): Read timed out

# Solution: Basic functionality still works
python test_setup.py  # ✅ Still works perfectly
python -m src.api.main  # Shows helpful error message: "FastAPI not available. Install with: pip install fastapi uvicorn"
```

### Database Connection Issues (EXPECTED)
```bash
python -m src.database.database check
# ❌ Database connection failed - PostgreSQL not available
# To start PostgreSQL: docker compose up -d db

# This is the correct behavior when PostgreSQL isn't running
```

### Missing .env File
```bash
./scripts/run_pipeline.sh --help
# ERROR: .env file not found. Please run setup.sh first.

# Solution:
cp .env.template .env
```

## Repository Structure and Key Files

### Root Directory
```
ai_investment_manager/
├── .env.template          # Environment configuration template
├── .env                   # Your environment config (create from template)
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies (may fail to install)
├── docker-compose.yml     # Docker services (PostgreSQL + web app)
├── test_setup.py          # Quick validation script - RUN THIS FIRST
├── src/                   # Main source code
├── scripts/               # Setup and utility scripts
├── logs/                  # Application logs (created automatically)
├── data/                  # Data storage (created automatically)
└── migrations/            # Database migrations
```

### Key Source Files
```
src/
├── api/main.py           # FastAPI application (requires fastapi installed)
├── config/settings.py    # Configuration management (works without dotenv)
├── data_pipeline/pipeline.py  # Data collection pipeline (stub implementation)
└── database/database.py  # Database management (stub implementation)
```

### Scripts
```
scripts/
├── setup.sh             # Main setup script (NEVER CANCEL - 15min timeout)
├── run_pipeline.sh      # Pipeline runner wrapper
└── setup_cron.sh        # Cron job installation
```

## Expected Build/Test Behavior

### What ALWAYS Works (No Dependencies Required)
- `python test_setup.py` ✅ (validated < 30ms)
- `python -c "from src.config.settings import config; print('OK')"` ✅ (validated instant)
- `python -m src.data_pipeline.pipeline init` ✅ (validated < 1s)
- `./scripts/run_pipeline.sh --help` ✅ (validated < 1s)
- `docker compose config` ✅ (validated < 100ms, shows version warning)

### What Requires Dependencies (May Fail in Restricted Environments)
- `python -m src.api.main` (needs fastapi/uvicorn)
- Full `pip install -r requirements.txt` (network timeouts expected)
- Database operations (need PostgreSQL running)

### What ALWAYS Fails Gracefully With Helpful Messages
- Missing API dependencies: "FastAPI not available. Install with: pip install fastapi uvicorn"
- Database commands: "PostgreSQL not available. To start PostgreSQL: docker compose up -d db"
- Missing .env: ".env file not found. Please run setup.sh first."

## Development Workflow - Start Here Every Time

1. **ALWAYS start with**: `python test_setup.py` (< 1 second)
2. **For API changes**: Try `python -m src.api.main` (install deps if needed)
3. **For pipeline changes**: Test with `python -m src.data_pipeline.pipeline --help`
4. **For config changes**: Test with `python -c "from src.config.settings import config; print(config.ENVIRONMENT)"`
5. **Before committing**: Run `python test_setup.py` to verify nothing broke

## Manual Validation Test Results

All commands tested and validated on Python 3.12.3:

```bash
# Quick validation (always run this first)
python test_setup.py  # ✅ < 30ms, 2/2 tests passed

# Configuration access
python -c "from src.config.settings import config; print('Config OK')"  # ✅ instant

# Pipeline commands
python -m src.data_pipeline.pipeline init    # ✅ < 1s
python -m src.data_pipeline.pipeline health  # ✅ < 1s

# Expected failures with helpful messages
python -m src.api.main                       # "FastAPI not available. Install with: pip install fastapi uvicorn"
python -m src.database.database check       # "PostgreSQL not available. To start PostgreSQL: docker compose up -d db"

# Docker validation
docker compose config  # ✅ < 100ms (shows version warning, this is normal)
```

## API Endpoints (when running with dependencies)

- `GET /` - API status and information
- `GET /health` - Health check
- `GET /config` - Configuration (non-sensitive values)

## Phase 1 Limitations - Current Implementation

- **Data pipeline**: Stub implementation (returns success messages, shows expected interface)
- **Database operations**: Require PostgreSQL (instructions provided when missing)
- **Full dependency install**: WILL fail in restricted networks (basic functionality still works)
- **Real data collection**: Not implemented (stubs show expected interface)

**This is a Phase 1 foundation** - future phases will add real data collection, AI analysis, and web interface. The current implementation provides a working foundation that can be built upon.