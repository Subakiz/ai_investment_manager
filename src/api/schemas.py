"""
Pydantic schemas for AlphaGen Investment Platform API
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal


class StockInfo(BaseModel):
    """Stock information schema"""
    id: int
    symbol: str
    company_name: str
    sector: Optional[str] = None
    subsector: Optional[str] = None
    is_lq45: bool = False
    market_cap: Optional[float] = None

    class Config:
        from_attributes = True


class QuantitativeScoreResponse(BaseModel):
    """Quantitative analysis scores response schema"""
    stock_id: int
    stock_symbol: str
    analysis_date: datetime
    
    # Valuation metrics
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    pe_relative_score: Optional[float] = None
    pb_relative_score: Optional[float] = None
    
    # Technical indicators
    rsi: Optional[float] = None
    rsi_score: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    ma_signal: Optional[str] = None
    ma_score: Optional[float] = None
    
    # Volume analysis
    volume_trend: Optional[str] = None
    volume_score: Optional[float] = None
    
    # Composite scores
    valuation_score: Optional[float] = None
    technical_score: Optional[float] = None
    composite_score: Optional[float] = None

    class Config:
        from_attributes = True


class QualitativeScoreResponse(BaseModel):
    """Aggregated qualitative/sentiment analysis response schema"""
    stock_symbol: str
    analysis_date: datetime
    average_sentiment: float = Field(..., description="Average sentiment score (-1.0 to 1.0)")
    average_confidence: float = Field(..., description="Average confidence (0.0 to 1.0)")
    sentiment_count: int = Field(..., description="Number of news articles analyzed")
    key_themes: List[str] = Field(default=[], description="Most common themes")
    qualitative_score: float = Field(..., description="Normalized qualitative score (0-100)")

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Daily recommendation response schema"""
    stock_id: int
    stock: StockInfo
    recommendation_date: datetime
    
    # Analysis scores
    quantitative_score: Optional[float] = None
    qualitative_score: Optional[float] = None
    combined_score: Optional[float] = None
    
    # Recommendation details
    recommendation: Optional[str] = None  # 'BUY', 'HOLD', 'SELL'
    confidence_level: Optional[str] = None  # 'HIGH', 'MEDIUM', 'LOW'
    price_target: Optional[float] = None
    
    # Supporting data
    key_themes: List[str] = Field(default=[], description="Key themes from analysis")
    technical_signals: Dict[str, Any] = Field(default={}, description="Technical analysis signals")
    risk_factors: List[str] = Field(default=[], description="Identified risk factors")

    class Config:
        from_attributes = True


class HistoricalScorePoint(BaseModel):
    """Single point in historical score data"""
    date: datetime
    quantitative_score: Optional[float] = None
    qualitative_score: Optional[float] = None
    combined_score: Optional[float] = None
    recommendation: Optional[str] = None

    class Config:
        from_attributes = True


class HistoricalScoresResponse(BaseModel):
    """Historical scores response schema"""
    stock_symbol: str
    period_days: int
    data_points: List[HistoricalScorePoint]
    summary: Dict[str, Any] = Field(default={}, description="Statistical summary of the period")

    class Config:
        from_attributes = True


class TradeRequest(BaseModel):
    """Trade request schema for portfolio operations"""
    action: str = Field(..., description="BUY or SELL")
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Price per share")
    trade_date: Optional[datetime] = None
    notes: Optional[str] = None


class Trade(BaseModel):
    """Trade response schema"""
    id: int
    portfolio_id: int
    stock_symbol: str
    action: str
    quantity: int
    price: float
    total_value: float
    trade_date: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class PortfolioHolding(BaseModel):
    """Portfolio holding schema"""
    stock_symbol: str
    company_name: str
    total_shares: int
    average_cost: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    """Portfolio response schema"""
    portfolio_name: str
    created_at: datetime
    total_cost: float
    current_value: Optional[float] = None
    total_pnl: Optional[float] = None
    total_pnl_percent: Optional[float] = None
    holdings: List[PortfolioHolding]
    recent_trades: List[Trade]

    class Config:
        from_attributes = True


class RiskScore(BaseModel):
    """Risk assessment response schema"""
    stock_symbol: str
    analysis_date: datetime
    volatility_30d: float = Field(..., description="30-day price volatility")
    risk_score: float = Field(..., description="Normalized risk score (0-100, higher = riskier)")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    beta: Optional[float] = None
    max_drawdown: Optional[float] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)