"""
News data collection pipeline for Indonesian financial news
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import asyncio
import re
from urllib.parse import urlparse
from newsapi import NewsApiClient
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..database.database import db_manager
from ..database.models import NewsArticle, NewsStockMention, Stock, DataIngestionLog
from ..utils.logger import get_pipeline_logger
from .lq45_stocks import LQ45_STOCKS, clean_idx_symbol
from ..config.settings import config

logger = get_pipeline_logger()

class NewsDataCollector:
    """Collect and store financial news data"""
    
    def __init__(self):
        self.newsapi_client = None
        if config.NEWS_API_KEY:
            self.newsapi_client = NewsApiClient(api_key=config.NEWS_API_KEY)
        
        # Indonesian financial news RSS feeds
        self.rss_feeds = [
            {
                'url': 'https://www.kontan.co.id/rss/investasi',
                'source': 'Kontan',
                'category': 'investment'
            },
            {
                'url': 'https://www.bisnis.com/rss/keuangan',
                'source': 'Bisnis.com',
                'category': 'finance'
            },
            {
                'url': 'https://finansial.bisnis.com/rss',
                'source': 'Bisnis.com',
                'category': 'finance'
            },
            {
                'url': 'https://www.cnnindonesia.com/ekonomi/rss',
                'source': 'CNN Indonesia',
                'category': 'economy'
            },
            {
                'url': 'https://www.detik.com/finance/rss',
                'source': 'Detik Finance',
                'category': 'finance'
            }
        ]
        
        # Keywords for Indonesian market
        self.market_keywords = [
            'idx', 'bei', 'bursa efek indonesia', 'saham', 'investasi',
            'lq45', 'ihsg', 'emiten', 'go public', 'ipo', 'dividen',
            'kapitalisasi pasar', 'volume perdagangan', 'pembukaan perdagangan',
            'penutupan perdagangan', 'suspensi', 'auto reject'
        ]
        
        # Company name mappings for stock mentions
        self.company_keywords = {}
        for symbol, company_name in LQ45_STOCKS:
            clean_symbol = clean_idx_symbol(symbol)
            self.company_keywords[clean_symbol.lower()] = symbol
            # Add company name keywords
            company_words = company_name.lower().split()
            for word in company_words:
                if len(word) > 3:  # Skip short words
                    self.company_keywords[word] = symbol
    
    async def collect_newsapi_articles(self, days_back: int = 1) -> Dict[str, int]:
        """Collect articles from NewsAPI"""
        if not self.newsapi_client:
            logger.warning("NewsAPI key not configured, skipping NewsAPI collection")
            return {'success': 0, 'failed': 0, 'total_records': 0}
        
        session_id = await self._log_start('newsapi_data')
        
        try:
            logger.info("Starting NewsAPI data collection")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            results = {
                'success': 0,
                'failed': 0,
                'total_records': 0
            }
            
            # Search for Indonesian market news
            keywords = [
                'Indonesia stock market',
                'IDX Indonesia',
                'Jakarta Stock Exchange',
                'Indonesian economy',
                'Bursa Efek Indonesia'
            ]
            
            async with db_manager.get_async_session() as session:
                for keyword in keywords:
                    try:
                        # Get articles from NewsAPI
                        articles = self.newsapi_client.get_everything(
                            q=keyword,
                            language='id',  # Indonesian
                            from_param=start_date.strftime('%Y-%m-%d'),
                            to=end_date.strftime('%Y-%m-%d'),
                            sort_by='publishedAt',
                            page_size=50
                        )
                        
                        if articles['status'] != 'ok':
                            logger.error(f"NewsAPI error: {articles.get('message', 'Unknown error')}")
                            continue
                        
                        for article_data in articles['articles']:
                            try:
                                # Check if article already exists
                                existing = await self._check_article_exists(session, article_data['url'])
                                if existing:
                                    continue
                                
                                # Create news article
                                article = await self._create_news_article(
                                    session,
                                    article_data,
                                    'NewsAPI'
                                )
                                
                                if article:
                                    results['total_records'] += 1
                                    results['success'] += 1
                                
                            except Exception as e:
                                logger.error(f"Error processing NewsAPI article: {e}")
                                results['failed'] += 1
                                continue
                        
                        await session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error fetching NewsAPI data for keyword '{keyword}': {e}")
                        continue
            
            await self._log_completion(session_id, results['total_records'])
            logger.info(f"NewsAPI collection completed. Success: {results['success']}, Failed: {results['failed']}, Total records: {results['total_records']}")
            
            return results
            
        except Exception as e:
            await self._log_error(session_id, str(e))
            logger.error(f"NewsAPI collection failed: {e}")
            raise
    
    async def collect_rss_articles(self, days_back: int = 1) -> Dict[str, int]:
        """Collect articles from RSS feeds"""
        session_id = await self._log_start('rss_data')
        
        try:
            logger.info(f"Starting RSS data collection from {len(self.rss_feeds)} feeds")
            
            results = {
                'success': 0,
                'failed': 0,
                'total_records': 0
            }
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            async with db_manager.get_async_session() as session:
                for feed_config in self.rss_feeds:
                    try:
                        logger.info(f"Processing RSS feed: {feed_config['source']}")
                        
                        # Parse RSS feed
                        feed = feedparser.parse(feed_config['url'])
                        
                        if feed.bozo:
                            logger.warning(f"RSS feed parsing warning for {feed_config['source']}: {feed.bozo_exception}")
                        
                        for entry in feed.entries:
                            try:
                                # Parse publication date
                                published_at = self._parse_rss_date(entry)
                                if not published_at or published_at < cutoff_date:
                                    continue
                                
                                # Check if article already exists
                                article_url = entry.get('link', entry.get('id', ''))
                                if not article_url:
                                    continue
                                
                                existing = await self._check_article_exists(session, article_url)
                                if existing:
                                    continue
                                
                                # Create article data structure
                                article_data = {
                                    'title': entry.get('title', ''),
                                    'description': entry.get('summary', entry.get('description', '')),
                                    'url': article_url,
                                    'publishedAt': published_at.isoformat(),
                                    'author': entry.get('author', ''),
                                    'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                                }
                                
                                # Create news article
                                article = await self._create_news_article(
                                    session,
                                    article_data,
                                    feed_config['source'],
                                    category=feed_config['category']
                                )
                                
                                if article:
                                    results['total_records'] += 1
                                
                            except Exception as e:
                                logger.error(f"Error processing RSS article from {feed_config['source']}: {e}")
                                results['failed'] += 1
                                continue
                        
                        await session.commit()
                        results['success'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing RSS feed {feed_config['source']}: {e}")
                        results['failed'] += 1
                        continue
            
            await self._log_completion(session_id, results['total_records'])
            logger.info(f"RSS collection completed. Success: {results['success']}, Failed: {results['failed']}, Total records: {results['total_records']}")
            
            return results
            
        except Exception as e:
            await self._log_error(session_id, str(e))
            logger.error(f"RSS collection failed: {e}")
            raise
    
    async def _create_news_article(self, session, article_data: Dict, source: str, category: str = 'market') -> Optional[NewsArticle]:
        """Create a news article record"""
        try:
            # Parse published date
            published_at = datetime.fromisoformat(
                article_data['publishedAt'].replace('Z', '+00:00')
            )
            
            # Calculate relevance score based on keywords
            relevance_score = self._calculate_relevance_score(
                article_data.get('title', '') + ' ' + article_data.get('description', '')
            )
            
            # Create article
            article = NewsArticle(
                title=article_data.get('title', '')[:500],  # Limit title length
                content=article_data.get('content', ''),
                summary=article_data.get('description', '')[:1000],  # Limit summary length
                url=article_data['url'],
                source=source,
                author=article_data.get('author', ''),
                published_at=published_at,
                category=category,
                relevance_score=relevance_score,
                language='id',  # Indonesian
                is_processed=False
            )
            
            session.add(article)
            await session.flush()  # Get the ID
            
            # Find stock mentions
            await self._find_stock_mentions(session, article)
            
            return article
            
        except Exception as e:
            logger.error(f"Error creating news article: {e}")
            return None
    
    async def _check_article_exists(self, session, url: str) -> bool:
        """Check if article with URL already exists"""
        stmt = select(NewsArticle).where(NewsArticle.url == url)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate relevance score based on keyword matching"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        keyword_matches = 0
        
        for keyword in self.market_keywords:
            if keyword in text_lower:
                keyword_matches += 1
        
        # Normalize score between 0.0 and 1.0
        max_possible_score = len(self.market_keywords)
        score = min(keyword_matches / max_possible_score * 2, 1.0)  # Multiply by 2 to boost scores
        
        return round(score, 2)
    
    async def _find_stock_mentions(self, session, article: NewsArticle):
        """Find and record stock mentions in article"""
        text = f"{article.title} {article.summary} {article.content}".lower()
        
        mentioned_stocks = set()
        
        for keyword, symbol in self.company_keywords.items():
            if keyword in text:
                mentioned_stocks.add(symbol)
        
        # Create stock mention records
        for symbol in mentioned_stocks:
            try:
                # Get stock ID
                stmt = select(Stock).where(Stock.symbol == symbol)
                result = await session.execute(stmt)
                stock = result.scalar_one_or_none()
                
                if stock:
                    # Count mentions
                    mention_count = text.count(keyword.lower())
                    
                    mention = NewsStockMention(
                        news_article_id=article.id,
                        stock_id=stock.id,
                        mention_count=mention_count,
                        sentiment_impact=0.0  # Will be calculated later by sentiment analysis
                    )
                    session.add(mention)
                    
            except Exception as e:
                logger.error(f"Error creating stock mention for {symbol}: {e}")
                continue
    
    def _parse_rss_date(self, entry) -> Optional[datetime]:
        """Parse publication date from RSS entry"""
        import time
        
        date_fields = ['published_parsed', 'updated_parsed']
        
        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_struct = getattr(entry, field)
                    return datetime(*time_struct[:6])
                except Exception:
                    continue
        
        # Try parsing date strings
        date_strings = [entry.get('published', ''), entry.get('updated', '')]
        
        for date_str in date_strings:
            if date_str:
                try:
                    # Common RSS date formats
                    for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    async def _log_start(self, process_type: str) -> int:
        """Log the start of a data ingestion process"""
        async with db_manager.get_async_session() as session:
            log_entry = DataIngestionLog(
                process_type=process_type,
                status='started',
                start_time=datetime.now()
            )
            session.add(log_entry)
            await session.commit()
            await session.refresh(log_entry)
            return log_entry.id
    
    async def _log_completion(self, log_id: int, records_processed: int):
        """Log the completion of a data ingestion process"""
        async with db_manager.get_async_session() as session:
            stmt = (
                update(DataIngestionLog)
                .where(DataIngestionLog.id == log_id)
                .values(
                    status='completed',
                    end_time=datetime.now(),
                    records_processed=records_processed
                )
            )
            await session.execute(stmt)
            await session.commit()
    
    async def _log_error(self, log_id: int, error_message: str):
        """Log an error in data ingestion process"""
        async with db_manager.get_async_session() as session:
            stmt = (
                update(DataIngestionLog)
                .where(DataIngestionLog.id == log_id)
                .values(
                    status='failed',
                    end_time=datetime.now(),
                    error_message=error_message
                )
            )
            await session.execute(stmt)
            await session.commit()

# CLI interface for manual news collection
async def main():
    """Main function for CLI usage"""
    import sys
    
    collector = NewsDataCollector()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "newsapi":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await collector.collect_newsapi_articles(days_back=days)
        elif command == "rss":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await collector.collect_rss_articles(days_back=days)
        elif command == "all":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await collector.collect_newsapi_articles(days_back=days)
            await collector.collect_rss_articles(days_back=days)
        else:
            print("Available commands: newsapi [days], rss [days], all [days]")
            sys.exit(1)
    else:
        print("Usage: python -m src.data_pipeline.news_data <command>")
        print("Commands: newsapi [days], rss [days], all [days]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())