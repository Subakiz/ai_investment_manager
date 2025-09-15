"""
FastAPI application for AlphaGen Investment Platform
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from ..database.database import get_async_db_session, db_manager
from ..database.models import (
    Stock, StockPrice, NewsArticle, DataIngestionLog,
    QuantitativeScores, SentimentAnalysis, DailyRecommendations,
    Portfolio, Trade
)
from ..data_pipeline.pipeline import DataPipeline
from ..utils.logger import get_logger
from ..config.settings import config
from ..analysis.risk import calculate_volatility_score
from .schemas import (
    RecommendationResponse, QuantitativeScoreResponse, QualitativeScoreResponse,
    HistoricalScoresResponse, HistoricalScorePoint, StockInfo, ErrorResponse,
    TradeRequest, Trade as TradeResponse, PortfolioResponse, PortfolioHolding,
    RiskScore
)
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import json

app = FastAPI(
    title="AlphaGen Investment Platform API",
    description="Personal AI Investment Platform for Indonesian Stock Market",
    version="1.0.0"
)

logger = get_logger(__name__)
pipeline = DataPipeline()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting AlphaGen API server")
    
    # Initialize database connection
    try:
        await db_manager.check_connection()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AlphaGen API server")
    await db_manager.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AlphaGen Personal Investment Platform API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = await pipeline.run_health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JSONResponse(content=health_status, status_code=status_code)
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )

@app.get("/stocks")
async def get_stocks(
    lq45_only: bool = True,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Get list of stocks"""
    try:
        query = select(Stock)
        if lq45_only:
            query = query.where(Stock.is_lq45 == True)
        
        result = await db.execute(query.order_by(Stock.symbol))
        stocks = result.scalars().all()
        
        return {
            "stocks": [
                {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "sector": stock.sector,
                    "is_lq45": stock.is_lq45,
                    "market_cap": float(stock.market_cap) if stock.market_cap else None
                }
                for stock in stocks
            ],
            "count": len(stocks)
        }
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stocks")

@app.get("/stocks/{symbol}/prices")
async def get_stock_prices(
    symbol: str,
    days: int = 30,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Get stock price history"""
    try:
        # Get stock
        stock_query = select(Stock).where(Stock.symbol == symbol)
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Get price data
        cutoff_date = datetime.now() - timedelta(days=days)
        prices_query = (
            select(StockPrice)
            .where(
                StockPrice.stock_id == stock.id,
                StockPrice.trade_date >= cutoff_date
            )
            .order_by(desc(StockPrice.trade_date))
        )
        
        prices_result = await db.execute(prices_query)
        prices = prices_result.scalars().all()
        
        return {
            "symbol": symbol,
            "company_name": stock.company_name,
            "prices": [
                {
                    "date": price.trade_date.strftime('%Y-%m-%d'),
                    "open": float(price.open_price),
                    "high": float(price.high_price),
                    "low": float(price.low_price),
                    "close": float(price.close_price),
                    "volume": price.volume,
                    "adjusted_close": float(price.adjusted_close) if price.adjusted_close else None
                }
                for price in prices
            ],
            "count": len(prices)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock prices for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock prices")

@app.get("/news")
async def get_news(
    days: int = 7,
    source: Optional[str] = None,
    relevance_threshold: float = 0.0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Get recent news articles"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = select(NewsArticle).where(
            NewsArticle.published_at >= cutoff_date,
            NewsArticle.relevance_score >= relevance_threshold
        )
        
        if source:
            query = query.where(NewsArticle.source == source)
        
        query = query.order_by(desc(NewsArticle.published_at)).limit(limit)
        
        result = await db.execute(query)
        articles = result.scalars().all()
        
        return {
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at.isoformat(),
                    "relevance_score": float(article.relevance_score) if article.relevance_score else 0.0,
                    "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
                    "category": article.category
                }
                for article in articles
            ],
            "count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")

@app.get("/pipeline/status")
async def get_pipeline_status(db: AsyncSession = Depends(get_async_db_session)):
    """Get data pipeline status"""
    try:
        # Get recent ingestion logs
        cutoff_date = datetime.now() - timedelta(days=7)
        
        query = (
            select(DataIngestionLog)
            .where(DataIngestionLog.start_time >= cutoff_date)
            .order_by(desc(DataIngestionLog.start_time))
            .limit(20)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Get statistics
        stats_query = select(
            DataIngestionLog.process_type,
            DataIngestionLog.status,
            func.count(DataIngestionLog.id).label('count')
        ).where(
            DataIngestionLog.start_time >= cutoff_date
        ).group_by(
            DataIngestionLog.process_type,
            DataIngestionLog.status
        )
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.all()
        
        return {
            "recent_logs": [
                {
                    "id": log.id,
                    "process_type": log.process_type,
                    "status": log.status,
                    "start_time": log.start_time.isoformat(),
                    "end_time": log.end_time.isoformat() if log.end_time else None,
                    "records_processed": log.records_processed,
                    "error_message": log.error_message
                }
                for log in logs
            ],
            "statistics": [
                {
                    "process_type": stat.process_type,
                    "status": stat.status,
                    "count": stat.count
                }
                for stat in stats
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pipeline status")

@app.post("/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    collection_type: str = "all",
    days_back: int = 1
):
    """Manually trigger data pipeline"""
    try:
        if collection_type not in ["all", "market", "news", "financials"]:
            raise HTTPException(status_code=400, detail="Invalid collection type")
        
        # Run pipeline in background
        background_tasks.add_task(
            pipeline.run_manual_collection,
            collection_type,
            days_back
        )
        
        return {
            "message": f"Pipeline triggered for {collection_type} collection",
            "collection_type": collection_type,
            "days_back": days_back,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger pipeline")


# Phase 3 API Endpoints

@app.get("/api/v1/recommendations/", response_model=List[RecommendationResponse])
async def get_latest_recommendations(
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns the latest list of daily recommendations for all stocks"""
    try:
        # Get the latest recommendation date
        latest_date_query = select(func.max(DailyRecommendations.recommendation_date))
        latest_date_result = await db.execute(latest_date_query)
        latest_date = latest_date_result.scalar()
        
        if not latest_date:
            return []
        
        # Get recommendations for the latest date
        query = (
            select(DailyRecommendations, Stock)
            .join(Stock, DailyRecommendations.stock_id == Stock.id)
            .where(DailyRecommendations.recommendation_date == latest_date)
            .order_by(desc(DailyRecommendations.combined_score))
            .limit(limit)
        )
        
        result = await db.execute(query)
        recommendations_with_stocks = result.all()
        
        response_data = []
        for recommendation, stock in recommendations_with_stocks:
            stock_info = StockInfo(
                id=stock.id,
                symbol=stock.symbol,
                company_name=stock.company_name,
                sector=stock.sector,
                subsector=stock.subsector,
                is_lq45=stock.is_lq45,
                market_cap=float(stock.market_cap) if stock.market_cap else None
            )
            
            # Parse JSON fields safely
            key_themes = []
            technical_signals = {}
            risk_factors = []
            
            try:
                if recommendation.key_themes:
                    key_themes = json.loads(recommendation.key_themes)
            except (json.JSONDecodeError, TypeError):
                pass
                
            try:
                if recommendation.technical_signals:
                    technical_signals = json.loads(recommendation.technical_signals)
            except (json.JSONDecodeError, TypeError):
                pass
                
            try:
                if recommendation.risk_factors:
                    risk_factors = json.loads(recommendation.risk_factors)
            except (json.JSONDecodeError, TypeError):
                pass
            
            response_data.append(RecommendationResponse(
                stock_id=recommendation.stock_id,
                stock=stock_info,
                recommendation_date=recommendation.recommendation_date,
                quantitative_score=float(recommendation.quantitative_score) if recommendation.quantitative_score else None,
                qualitative_score=float(recommendation.qualitative_score) if recommendation.qualitative_score else None,
                combined_score=float(recommendation.combined_score) if recommendation.combined_score else None,
                recommendation=recommendation.recommendation,
                confidence_level=recommendation.confidence_level,
                price_target=float(recommendation.price_target) if recommendation.price_target else None,
                key_themes=key_themes,
                technical_signals=technical_signals,
                risk_factors=risk_factors
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendations")


@app.get("/api/v1/recommendations/{symbol}", response_model=RecommendationResponse)
async def get_latest_recommendation_for_symbol(
    symbol: str,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns the latest recommendation for a single stock symbol"""
    try:
        # Find the stock first
        stock_query = select(Stock).where(Stock.symbol == symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
        
        # Get the latest recommendation for this stock
        query = (
            select(DailyRecommendations)
            .where(DailyRecommendations.stock_id == stock.id)
            .order_by(desc(DailyRecommendations.recommendation_date))
            .limit(1)
        )
        
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail=f"No recommendations found for symbol {symbol}")
        
        stock_info = StockInfo(
            id=stock.id,
            symbol=stock.symbol,
            company_name=stock.company_name,
            sector=stock.sector,
            subsector=stock.subsector,
            is_lq45=stock.is_lq45,
            market_cap=float(stock.market_cap) if stock.market_cap else None
        )
        
        # Parse JSON fields safely
        key_themes = []
        technical_signals = {}
        risk_factors = []
        
        try:
            if recommendation.key_themes:
                key_themes = json.loads(recommendation.key_themes)
        except (json.JSONDecodeError, TypeError):
            pass
            
        try:
            if recommendation.technical_signals:
                technical_signals = json.loads(recommendation.technical_signals)
        except (json.JSONDecodeError, TypeError):
            pass
            
        try:
            if recommendation.risk_factors:
                risk_factors = json.loads(recommendation.risk_factors)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return RecommendationResponse(
            stock_id=recommendation.stock_id,
            stock=stock_info,
            recommendation_date=recommendation.recommendation_date,
            quantitative_score=float(recommendation.quantitative_score) if recommendation.quantitative_score else None,
            qualitative_score=float(recommendation.qualitative_score) if recommendation.qualitative_score else None,
            combined_score=float(recommendation.combined_score) if recommendation.combined_score else None,
            recommendation=recommendation.recommendation,
            confidence_level=recommendation.confidence_level,
            price_target=float(recommendation.price_target) if recommendation.price_target else None,
            key_themes=key_themes,
            technical_signals=technical_signals,
            risk_factors=risk_factors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendation for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recommendation")


@app.get("/api/v1/scores/quantitative/{symbol}", response_model=QuantitativeScoreResponse)
async def get_quantitative_scores(
    symbol: str,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns the latest quantitative scores for a single stock symbol"""
    try:
        # Find the stock first
        stock_query = select(Stock).where(Stock.symbol == symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
        
        # Get the latest quantitative scores for this stock
        query = (
            select(QuantitativeScores)
            .where(QuantitativeScores.stock_id == stock.id)
            .order_by(desc(QuantitativeScores.analysis_date))
            .limit(1)
        )
        
        result = await db.execute(query)
        scores = result.scalar_one_or_none()
        
        if not scores:
            raise HTTPException(status_code=404, detail=f"No quantitative scores found for symbol {symbol}")
        
        return QuantitativeScoreResponse(
            stock_id=scores.stock_id,
            stock_symbol=stock.symbol,
            analysis_date=scores.analysis_date,
            pe_ratio=float(scores.pe_ratio) if scores.pe_ratio else None,
            pb_ratio=float(scores.pb_ratio) if scores.pb_ratio else None,
            pe_relative_score=float(scores.pe_relative_score) if scores.pe_relative_score else None,
            pb_relative_score=float(scores.pb_relative_score) if scores.pb_relative_score else None,
            rsi=float(scores.rsi) if scores.rsi else None,
            rsi_score=float(scores.rsi_score) if scores.rsi_score else None,
            ma_50=float(scores.ma_50) if scores.ma_50 else None,
            ma_200=float(scores.ma_200) if scores.ma_200 else None,
            ma_signal=scores.ma_signal,
            ma_score=float(scores.ma_score) if scores.ma_score else None,
            volume_trend=scores.volume_trend,
            volume_score=float(scores.volume_score) if scores.volume_score else None,
            valuation_score=float(scores.valuation_score) if scores.valuation_score else None,
            technical_score=float(scores.technical_score) if scores.technical_score else None,
            composite_score=float(scores.composite_score) if scores.composite_score else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quantitative scores for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quantitative scores")


@app.get("/api/v1/scores/qualitative/{symbol}", response_model=QualitativeScoreResponse)
async def get_qualitative_scores(
    symbol: str,
    days: int = 30,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns the latest aggregated qualitative sentiment for a single stock symbol"""
    try:
        # Find the stock first
        stock_query = select(Stock).where(Stock.symbol == symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sentiment analysis for news related to this stock
        # Note: This assumes news articles have stock relevance. You may need to adjust based on your schema
        query = (
            select(SentimentAnalysis, NewsArticle)
            .join(NewsArticle, SentimentAnalysis.news_article_id == NewsArticle.id)
            .where(
                and_(
                    NewsArticle.published_at >= start_date,
                    NewsArticle.published_at <= end_date,
                    # Assuming news articles are linked to stocks via content analysis
                    # You may need to adjust this based on your actual schema
                    NewsArticle.summary.ilike(f"%{stock.symbol}%")
                )
            )
        )
        
        result = await db.execute(query)
        sentiment_data = result.all()
        
        if not sentiment_data:
            # Return default response if no sentiment data found
            return QualitativeScoreResponse(
                stock_symbol=stock.symbol,
                analysis_date=end_date,
                average_sentiment=0.0,
                average_confidence=0.0,
                sentiment_count=0,
                key_themes=[],
                qualitative_score=50.0  # Neutral score
            )
        
        # Aggregate sentiment data
        total_sentiment = 0.0
        total_confidence = 0.0
        all_themes = []
        
        for sentiment, article in sentiment_data:
            total_sentiment += float(sentiment.sentiment_score)
            total_confidence += float(sentiment.confidence)
            
            try:
                if sentiment.themes:
                    themes = json.loads(sentiment.themes)
                    all_themes.extend(themes)
            except (json.JSONDecodeError, TypeError):
                pass
        
        count = len(sentiment_data)
        average_sentiment = total_sentiment / count
        average_confidence = total_confidence / count
        
        # Get most common themes (simple frequency count)
        from collections import Counter
        theme_counts = Counter(all_themes)
        key_themes = [theme for theme, count in theme_counts.most_common(5)]
        
        # Convert sentiment (-1 to 1) to qualitative score (0 to 100)
        qualitative_score = ((average_sentiment + 1) * 50)  # Maps -1->0, 0->50, 1->100
        
        return QualitativeScoreResponse(
            stock_symbol=stock.symbol,
            analysis_date=end_date,
            average_sentiment=average_sentiment,
            average_confidence=average_confidence,
            sentiment_count=count,
            key_themes=key_themes,
            qualitative_score=qualitative_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching qualitative scores for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch qualitative scores")


@app.get("/api/v1/history/scores/{symbol}", response_model=HistoricalScoresResponse)
async def get_historical_scores(
    symbol: str,
    days: int = 30,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns the historical composite scores for a stock over a specified time period"""
    try:
        # Find the stock first
        stock_query = select(Stock).where(Stock.symbol == symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get historical recommendations and quantitative scores
        recommendations_query = (
            select(DailyRecommendations)
            .where(
                and_(
                    DailyRecommendations.stock_id == stock.id,
                    DailyRecommendations.recommendation_date >= start_date,
                    DailyRecommendations.recommendation_date <= end_date
                )
            )
            .order_by(DailyRecommendations.recommendation_date)
        )
        
        result = await db.execute(recommendations_query)
        recommendations = result.scalars().all()
        
        # Convert to response format
        data_points = []
        for rec in recommendations:
            data_points.append(HistoricalScorePoint(
                date=rec.recommendation_date,
                quantitative_score=float(rec.quantitative_score) if rec.quantitative_score else None,
                qualitative_score=float(rec.qualitative_score) if rec.qualitative_score else None,
                combined_score=float(rec.combined_score) if rec.combined_score else None,
                recommendation=rec.recommendation
            ))
        
        # Calculate summary statistics
        summary = {}
        if data_points:
            combined_scores = [dp.combined_score for dp in data_points if dp.combined_score is not None]
            if combined_scores:
                summary = {
                    "min_score": min(combined_scores),
                    "max_score": max(combined_scores),
                    "avg_score": sum(combined_scores) / len(combined_scores),
                    "data_points_count": len(combined_scores),
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat()
                }
        
        return HistoricalScoresResponse(
            stock_symbol=stock.symbol,
            period_days=days,
            data_points=data_points,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical scores for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch historical scores")


# Portfolio Management Endpoints

@app.post("/api/v1/portfolio/{portfolio_name}/trade", response_model=TradeResponse)
async def add_trade_to_portfolio(
    portfolio_name: str,
    trade_request: TradeRequest,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Adds a trade (BUY/SELL) of a specific stock to a portfolio"""
    try:
        # Find or create portfolio
        portfolio_query = select(Portfolio).where(Portfolio.name == portfolio_name)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()
        
        if not portfolio:
            # Create new portfolio
            portfolio = Portfolio(name=portfolio_name)
            db.add(portfolio)
            await db.flush()  # Get the ID
        
        # Find the stock
        stock_query = select(Stock).where(Stock.symbol == trade_request.symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {trade_request.symbol} not found")
        
        # Validate action
        if trade_request.action.upper() not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Action must be 'BUY' or 'SELL'")
        
        # Calculate total value
        total_value = trade_request.quantity * trade_request.price
        
        # Create trade
        trade = Trade(
            portfolio_id=portfolio.id,
            stock_id=stock.id,
            action=trade_request.action.upper(),
            quantity=trade_request.quantity,
            price=trade_request.price,
            total_value=total_value,
            trade_date=trade_request.trade_date or datetime.now(),
            notes=trade_request.notes
        )
        
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        
        return TradeResponse(
            id=trade.id,
            portfolio_id=trade.portfolio_id,
            stock_symbol=stock.symbol,
            action=trade.action,
            quantity=trade.quantity,
            price=float(trade.price),
            total_value=float(trade.total_value),
            trade_date=trade.trade_date,
            notes=trade.notes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding trade to portfolio {portfolio_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add trade")


@app.get("/api/v1/portfolio/{portfolio_name}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_name: str,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Retrieves the current holdings and performance of a named portfolio"""
    try:
        # Find portfolio
        portfolio_query = select(Portfolio).where(Portfolio.name == portfolio_name)
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_name}' not found")
        
        # Get all trades for this portfolio
        trades_query = (
            select(Trade, Stock)
            .join(Stock, Trade.stock_id == Stock.id)
            .where(Trade.portfolio_id == portfolio.id)
            .order_by(desc(Trade.trade_date))
        )
        
        trades_result = await db.execute(trades_query)
        trades_with_stocks = trades_result.all()
        
        # Calculate holdings
        holdings_dict = {}
        total_cost = 0.0
        recent_trades = []
        
        for trade, stock in trades_with_stocks:
            symbol = stock.symbol
            
            # Add to recent trades (last 10)
            if len(recent_trades) < 10:
                recent_trades.append(TradeResponse(
                    id=trade.id,
                    portfolio_id=trade.portfolio_id,
                    stock_symbol=symbol,
                    action=trade.action,
                    quantity=trade.quantity,
                    price=float(trade.price),
                    total_value=float(trade.total_value),
                    trade_date=trade.trade_date,
                    notes=trade.notes
                ))
            
            # Calculate holdings
            if symbol not in holdings_dict:
                holdings_dict[symbol] = {
                    'company_name': stock.company_name,
                    'total_shares': 0,
                    'total_cost': 0.0,
                    'total_value': 0.0
                }
            
            if trade.action == 'BUY':
                holdings_dict[symbol]['total_shares'] += trade.quantity
                holdings_dict[symbol]['total_cost'] += float(trade.total_value)
                total_cost += float(trade.total_value)
            elif trade.action == 'SELL':
                holdings_dict[symbol]['total_shares'] -= trade.quantity
                holdings_dict[symbol]['total_cost'] -= float(trade.total_value)
                total_cost -= float(trade.total_value)
        
        # Get current prices for holdings
        holdings = []
        current_value = 0.0
        
        for symbol, holding_data in holdings_dict.items():
            if holding_data['total_shares'] > 0:  # Only include holdings with positive shares
                # Get latest price
                price_query = (
                    select(StockPrice)
                    .join(Stock, StockPrice.stock_id == Stock.id)
                    .where(Stock.symbol == symbol)
                    .order_by(desc(StockPrice.trade_date))
                    .limit(1)
                )
                
                price_result = await db.execute(price_query)
                latest_price = price_result.scalar_one_or_none()
                
                current_price = float(latest_price.close_price) if latest_price else None
                market_value = current_price * holding_data['total_shares'] if current_price else None
                average_cost = holding_data['total_cost'] / holding_data['total_shares'] if holding_data['total_shares'] > 0 else 0
                
                unrealized_pnl = None
                unrealized_pnl_percent = None
                
                if market_value and holding_data['total_cost'] > 0:
                    unrealized_pnl = market_value - holding_data['total_cost']
                    unrealized_pnl_percent = (unrealized_pnl / holding_data['total_cost']) * 100
                    current_value += market_value
                
                holdings.append(PortfolioHolding(
                    stock_symbol=symbol,
                    company_name=holding_data['company_name'],
                    total_shares=holding_data['total_shares'],
                    average_cost=average_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent
                ))
        
        # Calculate total P&L
        total_pnl = None
        total_pnl_percent = None
        
        if current_value > 0 and total_cost > 0:
            total_pnl = current_value - total_cost
            total_pnl_percent = (total_pnl / total_cost) * 100
        
        return PortfolioResponse(
            portfolio_name=portfolio.name,
            created_at=portfolio.created_at,
            total_cost=total_cost,
            current_value=current_value if current_value > 0 else None,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            holdings=holdings,
            recent_trades=recent_trades
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio {portfolio_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")


# Risk Analysis Endpoints

@app.get("/api/v1/risk/{symbol}", response_model=RiskScore)
async def get_risk_analysis(
    symbol: str,
    days: int = 30,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Returns risk analysis and volatility score for a stock symbol"""
    try:
        # Validate that the stock exists
        stock_query = select(Stock).where(Stock.symbol == symbol.upper())
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock with symbol {symbol} not found")
        
        # Calculate risk metrics
        risk_data = await calculate_volatility_score(symbol.upper(), days)
        
        return RiskScore(
            stock_symbol=risk_data['stock_symbol'],
            analysis_date=risk_data['analysis_date'],
            volatility_30d=risk_data['volatility_30d'],
            risk_score=risk_data['risk_score'],
            risk_level=risk_data['risk_level'],
            beta=risk_data.get('beta'),
            max_drawdown=risk_data.get('max_drawdown')
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating risk analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate risk analysis")


@app.get("/config")
async def get_config():
    """Get application configuration (non-sensitive values only)"""
    return {
        "environment": config.ENVIRONMENT,
        "timezone": config.TZ,
        "log_level": config.LOG_LEVEL,
        "market_update_time": config.LQ45_UPDATE_TIME,
        "news_update_time": config.NEWS_UPDATE_TIME,
        "database_configured": bool(config.DB_HOST and config.DB_NAME),
        "newsapi_configured": bool(config.NEWS_API_KEY),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.ENVIRONMENT == "development"
    )