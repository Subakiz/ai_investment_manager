"""
FastAPI application for AlphaGen Investment Platform
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import json

from ..database.database import get_async_db_session, db_manager
from ..database.models import (
    Stock, StockPrice, NewsArticle, DataIngestionLog,
    DailyRecommendations, QuantitativeScores, SentimentAnalysis, NewsStockMention
)
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

# Phase 3 Enhanced API Endpoints

@app.get("/recommendations/latest")
async def get_latest_recommendation(db: AsyncSession = Depends(get_async_db_session)):
    """Get the top-ranked stock recommendation for the most recent analysis date"""
    try:
        # Get the most recent recommendation date
        latest_date_query = select(func.max(DailyRecommendations.recommendation_date))
        result = await db.execute(latest_date_query)
        latest_date = result.scalar()
        
        if not latest_date:
            raise HTTPException(status_code=404, detail="No recommendations found")
        
        # Get the top recommendation for that date
        top_rec_query = (
            select(DailyRecommendations, Stock)
            .join(Stock)
            .where(DailyRecommendations.recommendation_date == latest_date)
            .order_by(desc(DailyRecommendations.combined_score))
            .limit(1)
        )
        
        result = await db.execute(top_rec_query)
        rec_data = result.first()
        
        if not rec_data:
            raise HTTPException(status_code=404, detail="No recommendations found for latest date")
        
        recommendation, stock = rec_data
        
        # Parse key themes from JSON
        key_themes = []
        if recommendation.key_themes:
            try:
                key_themes = json.loads(recommendation.key_themes)
            except json.JSONDecodeError:
                key_themes = []
        
        return {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "recommendation": recommendation.recommendation,
            "composite_score": float(recommendation.combined_score) if recommendation.combined_score else 0.0,
            "analysis_date": recommendation.recommendation_date.strftime('%Y-%m-%d'),
            "quantitative_score": float(recommendation.quantitative_score) if recommendation.quantitative_score else 0.0,
            "sentiment_score": float(recommendation.qualitative_score) if recommendation.qualitative_score else 0.0,
            "confidence": recommendation.confidence_level,
            "key_themes": key_themes[:5],  # Limit to top 5 themes
            "summary": f"Strong analytical signals with {recommendation.confidence_level.lower()} confidence on {recommendation.recommendation.lower()} recommendation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest recommendation")

@app.get("/stocks/{symbol}/analysis")
async def get_stock_analysis(symbol: str, db: AsyncSession = Depends(get_async_db_session)):
    """Get detailed analytical breakdown for a specific stock"""
    try:
        # Get stock
        stock_query = select(Stock).where(Stock.symbol == symbol)
        stock_result = await db.execute(stock_query)
        stock = stock_result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Get latest recommendation
        latest_rec_query = (
            select(DailyRecommendations)
            .where(DailyRecommendations.stock_id == stock.id)
            .order_by(desc(DailyRecommendations.recommendation_date))
            .limit(1)
        )
        rec_result = await db.execute(latest_rec_query)
        recommendation = rec_result.scalar_one_or_none()
        
        # Get latest quantitative scores
        latest_quant_query = (
            select(QuantitativeScores)
            .where(QuantitativeScores.stock_id == stock.id)
            .order_by(desc(QuantitativeScores.analysis_date))
            .limit(1)
        )
        quant_result = await db.execute(latest_quant_query)
        quant_scores = quant_result.scalar_one_or_none()
        
        # Get recent news articles
        cutoff_date = datetime.now() - timedelta(days=7)
        news_query = (
            select(NewsArticle, SentimentAnalysis)
            .outerjoin(SentimentAnalysis)
            .join(NewsStockMention)
            .where(
                NewsStockMention.stock_id == stock.id,
                NewsArticle.published_at >= cutoff_date
            )
            .order_by(desc(NewsArticle.published_at))
            .limit(10)
        )
        news_result = await db.execute(news_query)
        news_data = news_result.all()
        
        # Get recent price history
        price_query = (
            select(StockPrice)
            .where(
                StockPrice.stock_id == stock.id,
                StockPrice.trade_date >= cutoff_date
            )
            .order_by(desc(StockPrice.trade_date))
            .limit(7)
        )
        price_result = await db.execute(price_query)
        prices = price_result.scalars().all()
        
        # Build response
        latest_analysis = {}
        if recommendation:
            # Parse JSON fields
            key_themes = []
            if recommendation.key_themes:
                try:
                    key_themes = json.loads(recommendation.key_themes)
                except json.JSONDecodeError:
                    key_themes = []
            
            latest_analysis = {
                "analysis_date": recommendation.recommendation_date.strftime('%Y-%m-%d'),
                "quantitative_metrics": {
                    "pe_ratio": float(quant_scores.pe_ratio) if quant_scores and quant_scores.pe_ratio else None,
                    "pb_ratio": float(quant_scores.pb_ratio) if quant_scores and quant_scores.pb_ratio else None,
                    "rsi": float(quant_scores.rsi) if quant_scores and quant_scores.rsi else None,
                    "ma_signal": quant_scores.ma_signal if quant_scores else None,
                    "composite_score": float(recommendation.quantitative_score) if recommendation.quantitative_score else 0.0
                },
                "qualitative_metrics": {
                    "sentiment_score": float(recommendation.qualitative_score) if recommendation.qualitative_score else 0.0,
                    "confidence": recommendation.confidence_level,
                    "article_count": len(news_data),
                    "themes": key_themes[:5]
                }
            }
        
        recent_news = []
        for news_item in news_data:
            article, sentiment = news_item
            recent_news.append({
                "title": article.title,
                "sentiment_score": float(sentiment.sentiment_score) if sentiment and sentiment.sentiment_score else None,
                "confidence": float(sentiment.confidence) if sentiment and sentiment.confidence else None,
                "summary": sentiment.summary if sentiment else article.summary,
                "published_at": article.published_at.isoformat()
            })
        
        price_history = []
        for price in prices:
            price_history.append({
                "date": price.trade_date.strftime('%Y-%m-%d'),
                "close": float(price.close_price),
                "volume": price.volume
            })
        
        return {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "latest_analysis": latest_analysis,
            "recent_news": recent_news,
            "price_history": price_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock analysis")

@app.get("/market/sentiment")
async def get_market_sentiment(db: AsyncSession = Depends(get_async_db_session)):
    """Get high-level market mood overview"""
    try:
        # Get latest analysis date
        latest_date_query = select(func.max(DailyRecommendations.recommendation_date))
        result = await db.execute(latest_date_query)
        latest_date = result.scalar()
        
        if not latest_date:
            raise HTTPException(status_code=404, detail="No market data found")
        
        # Get all recommendations for latest date
        all_recs_query = (
            select(DailyRecommendations, Stock)
            .join(Stock)
            .where(DailyRecommendations.recommendation_date == latest_date)
        )
        result = await db.execute(all_recs_query)
        all_recs = result.all()
        
        if not all_recs:
            raise HTTPException(status_code=404, detail="No recommendations found for latest date")
        
        # Calculate overall sentiment
        total_sentiment = 0.0
        total_articles = 0
        sector_sentiment = {}
        
        for rec_data in all_recs:
            recommendation, stock = rec_data
            
            if recommendation.qualitative_score:
                # Convert 0-100 scale to -1 to 1 scale
                sentiment = (float(recommendation.qualitative_score) - 50) / 50
                total_sentiment += sentiment
                
                # Group by sector
                sector = stock.sector or "Unknown"
                if sector not in sector_sentiment:
                    sector_sentiment[sector] = []
                sector_sentiment[sector].append(sentiment)
        
        # Calculate averages
        overall_sentiment = total_sentiment / len(all_recs) if all_recs else 0.0
        
        # Aggregate sector sentiment
        sector_breakdown = {}
        for sector, sentiments in sector_sentiment.items():
            sector_breakdown[sector] = sum(sentiments) / len(sentiments)
        
        # Determine sentiment label
        if overall_sentiment > 0.3:
            sentiment_label = "Positive"
        elif overall_sentiment > 0.1:
            sentiment_label = "Moderately Positive"
        elif overall_sentiment > -0.1:
            sentiment_label = "Neutral"
        elif overall_sentiment > -0.3:
            sentiment_label = "Moderately Negative"
        else:
            sentiment_label = "Negative"
        
        # Get article count for recent period
        cutoff_date = latest_date - timedelta(days=1)
        article_count_query = select(func.count(NewsArticle.id)).where(
            NewsArticle.published_at >= cutoff_date
        )
        article_result = await db.execute(article_count_query)
        total_articles = article_result.scalar() or 0
        
        return {
            "overall_sentiment": round(overall_sentiment, 3),
            "sentiment_label": sentiment_label,
            "total_articles": total_articles,
            "analysis_date": latest_date.strftime('%Y-%m-%d'),
            "sector_breakdown": {k: round(v, 3) for k, v in sector_breakdown.items()},
            "trending_direction": "improving" if overall_sentiment > 0 else "declining"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market sentiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market sentiment")

@app.get("/themes/top")
async def get_top_themes(days: int = 2, db: AsyncSession = Depends(get_async_db_session)):
    """Get trending financial themes and narratives"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get recent recommendations with themes
        themes_query = (
            select(DailyRecommendations, Stock)
            .join(Stock)
            .where(
                DailyRecommendations.recommendation_date >= cutoff_date,
                DailyRecommendations.key_themes.isnot(None)
            )
        )
        result = await db.execute(themes_query)
        recommendations = result.all()
        
        # Process themes
        theme_stats = {}
        
        for rec_data in recommendations:
            recommendation, stock = rec_data
            
            try:
                themes = json.loads(recommendation.key_themes) if recommendation.key_themes else []
                sentiment = float(recommendation.qualitative_score) if recommendation.qualitative_score else 50
                # Convert to -1 to 1 scale
                sentiment_normalized = (sentiment - 50) / 50
                
                for theme in themes:
                    if isinstance(theme, str) and theme.strip():
                        theme_key = theme.lower().strip()
                        if theme_key not in theme_stats:
                            theme_stats[theme_key] = {
                                "theme": theme,
                                "occurrence_count": 0,
                                "sentiment_sum": 0.0,
                                "related_stocks": set()
                            }
                        
                        theme_stats[theme_key]["occurrence_count"] += 1
                        theme_stats[theme_key]["sentiment_sum"] += sentiment_normalized
                        theme_stats[theme_key]["related_stocks"].add(stock.symbol)
                        
            except json.JSONDecodeError:
                continue
        
        # Build top themes
        top_themes = []
        for theme_key, stats in theme_stats.items():
            if stats["occurrence_count"] >= 2:  # Only include themes mentioned at least twice
                avg_sentiment = stats["sentiment_sum"] / stats["occurrence_count"]
                top_themes.append({
                    "theme": stats["theme"],
                    "occurrence_count": stats["occurrence_count"],
                    "avg_sentiment": round(avg_sentiment, 3),
                    "related_stocks": list(stats["related_stocks"])[:5]  # Limit to 5 stocks
                })
        
        # Sort by occurrence count
        top_themes.sort(key=lambda x: x["occurrence_count"], reverse=True)
        
        return {
            "analysis_period": f"{cutoff_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            "top_themes": top_themes[:10]  # Return top 10 themes
        }
        
    except Exception as e:
        logger.error(f"Error fetching top themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top themes")

@app.get("/stocks/list")
async def get_stocks_with_scores(
    lq45_only: bool = True,
    db: AsyncSession = Depends(get_async_db_session)
):
    """Get list of all available stocks with current scores and recommendations"""
    try:
        # Get latest recommendation date
        latest_date_query = select(func.max(DailyRecommendations.recommendation_date))
        result = await db.execute(latest_date_query)
        latest_date = result.scalar()
        
        # Base query
        query = (
            select(Stock, DailyRecommendations)
            .outerjoin(
                DailyRecommendations,
                and_(
                    Stock.id == DailyRecommendations.stock_id,
                    DailyRecommendations.recommendation_date == latest_date
                )
            )
        )
        
        if lq45_only:
            query = query.where(Stock.is_lq45 == True)
        
        query = query.order_by(desc(DailyRecommendations.combined_score))
        
        result = await db.execute(query)
        stocks_data = result.all()
        
        stocks_list = []
        for stock_data in stocks_data:
            stock, recommendation = stock_data
            
            stock_info = {
                "id": stock.id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "is_lq45": stock.is_lq45,
                "market_cap": float(stock.market_cap) if stock.market_cap else None,
                "recommendation": None,
                "combined_score": None,
                "quantitative_score": None,
                "qualitative_score": None,
                "confidence": None
            }
            
            if recommendation:
                stock_info.update({
                    "recommendation": recommendation.recommendation,
                    "combined_score": float(recommendation.combined_score) if recommendation.combined_score else None,
                    "quantitative_score": float(recommendation.quantitative_score) if recommendation.quantitative_score else None,
                    "qualitative_score": float(recommendation.qualitative_score) if recommendation.qualitative_score else None,
                    "confidence": recommendation.confidence_level
                })
            
            stocks_list.append(stock_info)
        
        return {
            "stocks": stocks_list,
            "count": len(stocks_list),
            "analysis_date": latest_date.strftime('%Y-%m-%d') if latest_date else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching stocks list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stocks list")

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