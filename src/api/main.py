"""
FastAPI application for AlphaGen Investment Platform
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

from ..database.database import get_async_db_session, db_manager
from ..database.models import Stock, StockPrice, NewsArticle, DataIngestionLog
from ..data_pipeline.pipeline import DataPipeline
from ..utils.logger import get_logger
from ..config.settings import config
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

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