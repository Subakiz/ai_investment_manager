# AlphaGen Phase 2: Analytical Engine Implementation

## 🎯 Overview

Phase 2 of AlphaGen implements the analytical engine that transforms collected market and news data into actionable investment insights. This phase builds directly on the Phase 1 data collection foundation.

## ✨ New Features

### 📊 Quantitative Analysis Engine (`src/analysis/quantitative.py`)

**Core Capabilities:**
- **Market Data Processing**: Fetches latest prices and historical data from PostgreSQL
- **Technical Indicators**: RSI, moving averages (50-day, 200-day), volume trends
- **Valuation Metrics**: P/E and P/B ratios with relative scoring
- **Composite Scoring**: Weighted combination of all quantitative factors (0-100 scale)

**Key Functions:**
```python
# Fetch data
await analyzer.fetch_latest_market_data()
await analyzer.fetch_historical_data(symbol, days=252)

# Calculate metrics
technical_indicators = analyzer.calculate_technical_indicators(df)
valuation_metrics = analyzer.calculate_relative_valuation(symbol, financial_data, price)

# Run full analysis
results = await analyzer.run_quantitative_analysis()
```

### 🤖 Qualitative Analysis Engine (`src/analysis/qualitative.py`)

**Core Capabilities:**
- **Gemini AI Integration**: Uses Google Gemini 2.5 Pro for sentiment analysis
- **Structured Output**: Returns JSON with sentiment scores, confidence, themes, and summaries
- **Batch Processing**: Efficiently processes multiple articles
- **Indonesian Language Support**: Handles both Indonesian and English financial news

**Key Functions:**
```python
# Initialize Gemini client
analyzer.initialize_gemini_client()

# Analyze single article
result = await analyzer.analyze_article_sentiment(article_text, symbol)

# Batch process articles
results = await analyzer.batch_analyze_articles(articles)

# Run full analysis
summary = await analyzer.run_qualitative_analysis(hours_back=24)
```

**Example Output:**
```json
{
  "sentiment_score": 0.75,
  "confidence": 0.89,
  "themes": ["digital banking", "loan growth"],
  "summary": "Positive earnings outlook with strong digital transformation progress",
  "relevance": 0.92
}
```

### 🔄 Enhanced Pipeline Integration

**New Scheduled Workflow:**
1. **4:30 PM WIB**: Market data collection (existing)
2. **4:45 PM WIB**: News data collection (existing)
3. **5:00 PM WIB**: 🆕 Quantitative analysis
4. **5:15 PM WIB**: 🆕 Qualitative analysis
5. **5:30 PM WIB**: 🆕 Generate daily recommendations

**New CLI Commands:**
```bash
# Run individual analysis
python -m src.data_pipeline.pipeline analyze-quantitative
python -m src.data_pipeline.pipeline analyze-qualitative

# Run combined analysis
python -m src.data_pipeline.pipeline analyze-all

# Test individual modules
python -m src.analysis.quantitative analyze
python -m src.analysis.qualitative analyze
```

### 🗄️ New Database Tables

**QuantitativeScores Table:**
- Daily quantitative metrics per stock
- P/E, P/B ratios with relative scores
- Technical indicators (RSI, moving averages)
- Composite scores (0-100)

**SentimentAnalysis Table:**
- AI-processed sentiment results
- Confidence scores and themes
- Processing metadata

**DailyRecommendations Table:**
- Final ranked stock recommendations
- Combined quantitative and qualitative scores
- BUY/HOLD/SELL recommendations with confidence levels

**Enhanced NewsArticle Table:**
- Additional sentiment analysis fields
- AI-generated summaries
- Processing timestamps

## 🚀 Quick Start

### Prerequisites

1. **Database Setup**: Ensure PostgreSQL is running with Phase 1 data
2. **API Keys**: Add `GEMINI_API_KEY` to your `.env` file
3. **Dependencies**: Install additional packages:
```bash
pip install google-generativeai pandas numpy schedule
```

### Running Analysis

1. **Test Installation:**
```bash
python demo_analysis.py all
```

2. **Run Quantitative Analysis:**
```bash
python -m src.analysis.quantitative analyze
```

3. **Run Qualitative Analysis:**
```bash
python -m src.analysis.qualitative analyze
```

4. **Run Full Pipeline:**
```bash
python -m src.data_pipeline.pipeline analyze-all
```

## 📋 Configuration

### Environment Variables (.env)

Add these new variables to your `.env` file:

```bash
# AI Analysis
GEMINI_API_KEY=your_gemini_api_key_here

# Analysis Timing (optional)
QUANTITATIVE_ANALYSIS_TIME=10:00  # UTC time
QUALITATIVE_ANALYSIS_TIME=10:15   # UTC time
```

### Analysis Parameters

**Quantitative Analysis:**
- Historical data window: 252 days (1 year)
- RSI period: 14 days
- Moving averages: 50-day, 200-day
- Scoring weights: 40% valuation, 60% technical

**Qualitative Analysis:**
- Article processing window: 24 hours
- Batch size: 100 articles
- Rate limiting: 1 second between API calls
- Confidence threshold: 0.3

## 📊 Analysis Output

### Quantitative Scores (0-100 scale)
- **Valuation Score**: Based on P/E and P/B ratios
- **Technical Score**: RSI, moving averages, volume trends
- **Composite Score**: Weighted combination

### Qualitative Scores (-1.0 to 1.0 scale)
- **Sentiment Score**: Overall article sentiment
- **Confidence**: AI analysis confidence
- **Relevance**: Relevance to stock price movement
- **Themes**: Key business/financial concepts

### Daily Recommendations
- **BUY**: Composite score > 70
- **HOLD**: Composite score 40-70
- **SELL**: Composite score < 40

## 🔍 Indonesian Market Considerations

**Quantitative Analysis:**
- IDR currency handling in calculations
- Jakarta Stock Exchange (JKSE) benchmarks
- Local market holiday awareness
- LQ45 index focus

**Qualitative Analysis:**
- Indonesian language news processing
- Local financial terminology recognition
- Bahasa Indonesia sentiment understanding
- Indonesian business context awareness

## 🎯 Success Metrics

**Quantitative Engine:**
- ✅ Daily analysis of all 45 LQ45 stocks
- ✅ Composite scores (0-100) for each stock
- ✅ Historical trend analysis
- ✅ Technical indicator calculations

**Qualitative Engine:**
- ✅ Gemini API integration with structured JSON output
- ✅ Daily sentiment analysis of relevant news
- ✅ Theme extraction and company-specific aggregation
- ✅ Indonesian language support

**Pipeline Integration:**
- ✅ Automated analysis after data collection
- ✅ Error handling and monitoring
- ✅ CLI commands for manual analysis
- ✅ Enhanced scheduling system

## 🚧 Next Steps (Phase 3)

1. **FastAPI Endpoints**: Serve analysis results via REST API
2. **Dashboard Integration**: Visualize analysis results
3. **Portfolio Tracking**: Track performance of recommendations
4. **Advanced Analytics**: Risk scoring, correlation analysis
5. **Real-time Updates**: Streaming analysis capabilities

## 💰 Cost Considerations

**Gemini API Usage:**
- Estimated cost: $30-70/month
- ~45 stocks × ~10 articles/day × 30 days
- Rate limiting reduces costs
- Confidence thresholds optimize usage

## 🔧 Troubleshooting

**Common Issues:**

1. **"No module named 'google.generativeai'"**
   ```bash
   pip install google-generativeai
   ```

2. **"GEMINI_API_KEY not found"**
   - Add API key to `.env` file
   - Get key from Google AI Studio

3. **"No historical data found"**
   - Ensure Phase 1 data collection is working
   - Check database connection

4. **Analysis timeouts:**
   - Increase rate limiting delays
   - Reduce batch sizes
   - Check network connection

## 📞 Support

For issues specific to Phase 2 analysis engines:
1. Check the demo script: `python demo_analysis.py`
2. Review logs in `logs/` directory
3. Validate database connectivity
4. Verify API key configuration

---

**Phase 2 Status**: ✅ **COMPLETED**
- Quantitative analysis engine implemented
- Qualitative analysis with Gemini AI integrated
- Enhanced pipeline with automated analysis
- New database tables and CLI commands added
- Ready for Phase 3 API and dashboard development
