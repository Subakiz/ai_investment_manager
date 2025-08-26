# AlphaGen Personal Investment Platform

Welcome to the AlphaGen Personal Investment Platform! This is a Phase 1 implementation of an AI-powered investment platform focused on the Indonesian Stock Exchange (IDX), specifically designed for personal use.

## 🎯 Project Overview

AlphaGen is a personal AI investment platform that automatically collects and analyzes Indonesian stock market data and financial news. This Phase 1 implementation provides the foundation for data collection and storage.

### Current Features (Phase 1)

- **Automated Data Collection**: Daily collection of LQ45 stock prices and Indonesian financial news
- **Database Management**: PostgreSQL with TimescaleDB for time-series data and pgvector for text embeddings
- **Market Data Pipeline**: OHLCV data for top 45 liquid Indonesian stocks
- **News Data Pipeline**: Financial news from Indonesian sources (Kontan, Bisnis.com, etc.)
- **Scheduling & Automation**: Cron-based scheduling for daily data collection
- **Health Monitoring**: Pipeline monitoring and error handling
- **REST API**: Basic endpoints for data access and pipeline management

### Technology Stack

- **Language**: Python 3.11+
- **Database**: PostgreSQL 14+ with TimescaleDB and pgvector extensions
- **Web Framework**: FastAPI
- **Data Sources**: Yahoo Finance (yfinance), NewsAPI, RSS feeds
- **Task Scheduling**: Cron jobs
- **Containerization**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ (or use Docker Compose)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Subakiz/ai_investment_manager.git
   cd ai_investment_manager
   ```

2. **Run the setup script**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   nano .env
   ```

4. **Start the database** (using Docker):
   ```bash
   docker-compose up -d db
   ```

5. **Run database migration**:
   ```bash
   python migrations/001_initial_schema.py
   ```

6. **Initialize the data pipeline**:
   ```bash
   python -m src.data_pipeline.pipeline init
   ```

### Running the Application

#### Start the API Server
```bash
python -m src.api.main
```
Access the API at: http://localhost:8000

#### Manual Data Collection
```bash
# Collect all data for the last day
python -m src.data_pipeline.pipeline collect --type all --days 1

# Collect only market data
python -m src.data_pipeline.pipeline collect --type market --days 1

# Collect only news data
python -m src.data_pipeline.pipeline collect --type news --days 1
```

#### Start Automated Scheduling
```bash
# For continuous automated collection
python -m src.data_pipeline.pipeline schedule
```

#### Setup Cron Jobs
```bash
# For production deployment with cron
./scripts/setup_cron.sh
```

## 📊 Data Collection

### Market Data
- **Source**: Yahoo Finance
- **Stocks**: LQ45 index constituents (top 45 liquid Indonesian stocks)
- **Data**: Daily OHLCV, financial statements
- **Schedule**: Daily at 4:30 PM WIB (after IDX close)

### News Data
- **Sources**: NewsAPI, Indonesian financial RSS feeds
- **Keywords**: IDX, Indonesian market, LQ45 companies
- **Processing**: Relevance scoring, stock mention detection
- **Schedule**: Daily at 4:45 PM WIB

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alphagen
DB_USER=alphauser
DB_PASSWORD=alphapass

# API Keys
NEWS_API_KEY=your_newsapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Data Pipeline Configuration
LQ45_UPDATE_TIME=09:30  # UTC time (4:30 PM WIB)
NEWS_UPDATE_TIME=09:45  # UTC time (4:45 PM WIB)

# Application Settings
LOG_LEVEL=INFO
TZ=Asia/Jakarta
ENVIRONMENT=development
```

## 🏗️ Project Structure

```
ai_investment_manager/
├── src/
│   ├── api/                 # FastAPI application
│   ├── config/              # Configuration management
│   ├── database/            # Database models and connections
│   ├── data_pipeline/       # Data collection pipelines
│   └── utils/               # Utility functions and logging
├── scripts/                 # Setup and deployment scripts
├── migrations/              # Database migration scripts
├── logs/                    # Application logs
├── data/                    # Temporary data storage
├── docker-compose.yml       # Docker services configuration
├── requirements.txt         # Python dependencies
└── .env.template           # Environment configuration template
```

## 📈 API Endpoints

- `GET /` - API status and information
- `GET /health` - Health check endpoint
- `GET /stocks` - List of LQ45 stocks
- `GET /stocks/{symbol}/prices` - Stock price history
- `GET /news` - Recent financial news
- `GET /pipeline/status` - Data pipeline status
- `POST /pipeline/run` - Manually trigger data collection

## 🔍 Monitoring and Logs

### Log Files
- `logs/alphagen.log` - General application logs
- `logs/data_pipeline.log` - Data pipeline operations
- `logs/market_data.log` - Market data collection
- `logs/news_data.log` - News data collection

### Health Checks
```bash
# Check pipeline health
python -m src.data_pipeline.pipeline health

# Check via API
curl http://localhost:8000/health
```

## 🛠️ Development

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run tests (when implemented)
pytest tests/
```

### Database Management
```bash
# Initialize database
python -m src.database.database init

# Check database connection
python -m src.database.database check

# Create tables only
python -m src.database.database create-tables
```

## 🚧 Roadmap

### Phase 2 (Weeks 4-6)
- Quantitative analysis engine
- Gemini AI integration for insights
- Sentiment analysis for news

### Phase 3 (Weeks 7-9)
- Enhanced FastAPI backend
- Streamlit dashboard
- Portfolio tracking

### Phase 4 (Weeks 10-12)
- Full automation
- Paper trading validation
- Performance optimization

## 🔒 Security Notes

- Store sensitive configuration in `.env` file (not in version control)
- Use environment-specific database credentials
- Secure API endpoints in production
- Regular log rotation and cleanup

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check logs in the `logs/` directory
- Review configuration in `.env` file

---

**Note**: This is Phase 1 implementation focusing on data collection foundation. Future phases will add AI analysis, web interface, and trading capabilities.
