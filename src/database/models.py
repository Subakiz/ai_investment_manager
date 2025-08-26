"""
Database models for AlphaGen Investment Platform
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, Text, Boolean, 
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class Stock(Base):
    """Stock master data table"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    subsector = Column(String(100))
    is_lq45 = Column(Boolean, default=False, index=True)
    market_cap = Column(Numeric(20, 2))
    currency = Column(String(3), default='IDR')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    stock_prices = relationship("StockPrice", back_populates="stock")
    financial_statements = relationship("FinancialStatement", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', company_name='{self.company_name}')>"

class StockPrice(Base):
    """Daily stock price data (OHLCV) - TimescaleDB hypertable"""
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(DateTime, nullable=False)
    open_price = Column(Numeric(15, 2), nullable=False)
    high_price = Column(Numeric(15, 2), nullable=False)
    low_price = Column(Numeric(15, 2), nullable=False)
    close_price = Column(Numeric(15, 2), nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="stock_prices")
    
    # Indexes
    __table_args__ = (
        Index("idx_stock_prices_stock_date", "stock_id", "trade_date"),
        Index("idx_stock_prices_date", "trade_date"),
        UniqueConstraint("stock_id", "trade_date", name="uq_stock_price_date"),
    )
    
    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date='{self.trade_date}', close={self.close_price})>"

class FinancialStatement(Base):
    """Quarterly/Annual financial statements"""
    __tablename__ = "financial_statements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    statement_type = Column(String(20), nullable=False)  # 'quarterly', 'annual'
    period_end = Column(DateTime, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer)  # 1,2,3,4 for quarterly
    
    # Income Statement
    revenue = Column(Numeric(20, 2))
    gross_profit = Column(Numeric(20, 2))
    operating_income = Column(Numeric(20, 2))
    net_income = Column(Numeric(20, 2))
    ebitda = Column(Numeric(20, 2))
    
    # Balance Sheet
    total_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    total_equity = Column(Numeric(20, 2))
    cash_and_equivalents = Column(Numeric(20, 2))
    
    # Cash Flow Statement
    operating_cash_flow = Column(Numeric(20, 2))
    investing_cash_flow = Column(Numeric(20, 2))
    financing_cash_flow = Column(Numeric(20, 2))
    
    # Ratios
    eps = Column(Numeric(10, 4))  # Earnings per share
    pe_ratio = Column(Numeric(10, 2))
    pb_ratio = Column(Numeric(10, 2))
    roe = Column(Numeric(10, 4))  # Return on equity
    roa = Column(Numeric(10, 4))  # Return on assets
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="financial_statements")
    
    # Indexes
    __table_args__ = (
        Index("idx_financial_statements_stock_period", "stock_id", "period_end"),
        Index("idx_financial_statements_period", "period_end"),
        UniqueConstraint("stock_id", "statement_type", "period_end", name="uq_financial_statement"),
    )
    
    def __repr__(self):
        return f"<FinancialStatement(stock_id={self.stock_id}, period='{self.period_end}', type='{self.statement_type}')>"

class NewsArticle(Base):
    """News articles and sentiment data"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(Text, unique=True, nullable=False)
    source = Column(String(100), nullable=False)
    author = Column(String(255))
    published_at = Column(DateTime, nullable=False, index=True)
    
    # Categorization
    category = Column(String(50))  # 'market', 'company', 'economic', 'political'
    relevance_score = Column(Numeric(3, 2))  # 0.0 to 1.0
    
    # Sentiment analysis (enhanced for qualitative engine)
    sentiment_score = Column(Numeric(3, 2))  # -1.0 to 1.0
    sentiment_label = Column(String(20))  # 'positive', 'negative', 'neutral'
    confidence = Column(Numeric(3, 2))  # 0.0 to 1.0 from AI analysis
    themes = Column(Text)  # JSON array of extracted themes
    ai_summary = Column(Text)  # AI-generated summary
    processed_at = Column(DateTime)  # When sentiment analysis was completed
    
    # Text embeddings for similarity search (pgvector)
    embedding = Column(Text)  # JSON serialized vector
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    language = Column(String(5), default='id')  # 'id' for Indonesian, 'en' for English
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    stock_mentions = relationship("NewsStockMention", back_populates="news_article")
    
    # Indexes
    __table_args__ = (
        Index("idx_news_articles_published", "published_at"),
        Index("idx_news_articles_source", "source"),
        Index("idx_news_articles_processed", "is_processed"),
    )
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:50]}...', source='{self.source}')>"

class NewsStockMention(Base):
    """Junction table for news articles mentioning specific stocks"""
    __tablename__ = "news_stock_mentions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    news_article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    mention_count = Column(Integer, default=1)
    sentiment_impact = Column(Numeric(3, 2))  # Impact score for this specific stock
    
    # Relationships
    news_article = relationship("NewsArticle", back_populates="stock_mentions")
    stock = relationship("Stock")
    
    # Indexes
    __table_args__ = (
        Index("idx_news_stock_mentions_news", "news_article_id"),
        Index("idx_news_stock_mentions_stock", "stock_id"),
        UniqueConstraint("news_article_id", "stock_id", name="uq_news_stock_mention"),
    )

class DataIngestionLog(Base):
    """Log table for tracking data ingestion operations"""
    __tablename__ = "data_ingestion_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    process_type = Column(String(50), nullable=False)  # 'market_data', 'news_data'
    status = Column(String(20), nullable=False)  # 'started', 'completed', 'failed'
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    process_metadata = Column(Text)  # JSON for additional info
    
    # Indexes
    __table_args__ = (
        Index("idx_data_ingestion_logs_type", "process_type"),
        Index("idx_data_ingestion_logs_status", "status"),
        Index("idx_data_ingestion_logs_time", "start_time"),
    )
    
    def __repr__(self):
        return f"<DataIngestionLog(type='{self.process_type}', status='{self.status}', time='{self.start_time}')>"

class QuantitativeScores(Base):
    """Daily quantitative analysis scores for stocks"""
    __tablename__ = "quantitative_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    analysis_date = Column(DateTime, nullable=False)
    
    # Valuation metrics
    pe_ratio = Column(Numeric(10, 2))
    pb_ratio = Column(Numeric(10, 2))
    pe_relative_score = Column(Numeric(5, 2))  # 0-100 score vs historical/industry
    pb_relative_score = Column(Numeric(5, 2))  # 0-100 score vs historical/industry
    
    # Technical indicators
    rsi = Column(Numeric(5, 2))  # 0-100
    rsi_score = Column(Numeric(5, 2))  # 0-100 score based on RSI
    ma_50 = Column(Numeric(15, 2))  # 50-day moving average
    ma_200 = Column(Numeric(15, 2))  # 200-day moving average
    ma_signal = Column(String(10))  # 'bullish', 'bearish', 'neutral'
    ma_score = Column(Numeric(5, 2))  # 0-100 score based on MA position
    
    # Volume analysis
    volume_trend = Column(String(10))  # 'increasing', 'decreasing', 'stable'
    volume_score = Column(Numeric(5, 2))  # 0-100 score based on volume
    
    # Composite scores
    valuation_score = Column(Numeric(5, 2))  # 0-100 composite valuation
    technical_score = Column(Numeric(5, 2))  # 0-100 composite technical
    composite_score = Column(Numeric(5, 2))  # 0-100 overall quantitative score
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    stock = relationship("Stock")
    
    # Indexes
    __table_args__ = (
        Index("idx_quantitative_scores_stock_date", "stock_id", "analysis_date"),
        Index("idx_quantitative_scores_date", "analysis_date"),
        Index("idx_quantitative_scores_composite", "composite_score"),
        UniqueConstraint("stock_id", "analysis_date", name="uq_quantitative_score_date"),
    )
    
    def __repr__(self):
        return f"<QuantitativeScores(stock_id={self.stock_id}, date='{self.analysis_date}', score={self.composite_score})>"

class SentimentAnalysis(Base):
    """Processed sentiment analysis results for news articles"""
    __tablename__ = "sentiment_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    news_article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    
    # Gemini analysis results
    sentiment_score = Column(Numeric(3, 2), nullable=False)  # -1.0 to 1.0
    confidence = Column(Numeric(3, 2), nullable=False)  # 0.0 to 1.0
    themes = Column(Text)  # JSON array of themes
    summary = Column(Text)  # Brief summary from AI
    relevance = Column(Numeric(3, 2))  # 0.0 to 1.0 relevance to stock price
    
    # Processing metadata
    model_used = Column(String(50), default="gemini-2.5-pro")
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    news_article = relationship("NewsArticle")
    
    # Indexes
    __table_args__ = (
        Index("idx_sentiment_analysis_article", "news_article_id"),
        Index("idx_sentiment_analysis_sentiment", "sentiment_score"),
        Index("idx_sentiment_analysis_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<SentimentAnalysis(article_id={self.news_article_id}, sentiment={self.sentiment_score}, confidence={self.confidence})>"

class DailyRecommendations(Base):
    """Daily ranked stock recommendations based on combined analysis"""
    __tablename__ = "daily_recommendations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    recommendation_date = Column(DateTime, nullable=False)
    
    # Analysis scores
    quantitative_score = Column(Numeric(5, 2))  # 0-100
    qualitative_score = Column(Numeric(5, 2))  # 0-100 from news sentiment
    combined_score = Column(Numeric(5, 2))  # 0-100 final weighted score
    
    # Recommendation details
    recommendation = Column(String(10))  # 'BUY', 'HOLD', 'SELL'
    confidence_level = Column(String(10))  # 'HIGH', 'MEDIUM', 'LOW'
    price_target = Column(Numeric(15, 2))  # Estimated target price
    
    # Supporting data
    key_themes = Column(Text)  # JSON array of key themes from news
    technical_signals = Column(Text)  # JSON object of technical signals
    risk_factors = Column(Text)  # JSON array of identified risks
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    stock = relationship("Stock")
    
    # Indexes
    __table_args__ = (
        Index("idx_daily_recommendations_stock_date", "stock_id", "recommendation_date"),
        Index("idx_daily_recommendations_date", "recommendation_date"),
        Index("idx_daily_recommendations_score", "combined_score"),
        Index("idx_daily_recommendations_rec", "recommendation"),
        UniqueConstraint("stock_id", "recommendation_date", name="uq_daily_recommendation_date"),
    )
    
    def __repr__(self):
        return f"<DailyRecommendations(stock_id={self.stock_id}, date='{self.recommendation_date}', rec='{self.recommendation}', score={self.combined_score})>"