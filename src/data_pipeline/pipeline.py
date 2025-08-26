"""
Main data pipeline orchestrator and scheduler
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import signal
import sys

from .market_data import MarketDataCollector
from .news_data import NewsDataCollector
from ..database.database import init_database
from ..utils.logger import get_pipeline_logger
from ..config.settings import config

logger = get_pipeline_logger()

class DataPipeline:
    """Main data pipeline orchestrator"""
    
    def __init__(self):
        self.market_collector = MarketDataCollector()
        self.news_collector = NewsDataCollector()
        self.running = False
    
    async def initialize(self):
        """Initialize the data pipeline"""
        logger.info("Initializing AlphaGen data pipeline...")
        
        try:
            # Initialize database
            await init_database()
            
            # Initialize stocks
            await self.market_collector.initialize_stocks()
            
            logger.info("Data pipeline initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Data pipeline initialization failed: {e}")
            return False
    
    async def run_daily_market_data_collection(self):
        """Run daily market data collection"""
        logger.info("Starting scheduled market data collection")
        
        try:
            results = await self.market_collector.collect_daily_prices(days_back=1)
            logger.info(f"Market data collection completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Market data collection failed: {e}")
            return {'success': 0, 'failed': 1, 'total_records': 0}
    
    async def run_daily_news_collection(self):
        """Run daily news data collection"""
        logger.info("Starting scheduled news data collection")
        
        try:
            # Collect from both NewsAPI and RSS feeds
            newsapi_results = await self.news_collector.collect_newsapi_articles(days_back=1)
            rss_results = await self.news_collector.collect_rss_articles(days_back=1)
            
            # Combine results
            total_results = {
                'success': newsapi_results['success'] + rss_results['success'],
                'failed': newsapi_results['failed'] + rss_results['failed'],
                'total_records': newsapi_results['total_records'] + rss_results['total_records']
            }
            
            logger.info(f"News data collection completed: {total_results}")
            return total_results
            
        except Exception as e:
            logger.error(f"News data collection failed: {e}")
            return {'success': 0, 'failed': 1, 'total_records': 0}
    
    async def run_weekly_financial_statements_collection(self):
        """Run weekly financial statements collection"""
        logger.info("Starting scheduled financial statements collection")
        
        try:
            results = await self.market_collector.collect_financial_statements()
            logger.info(f"Financial statements collection completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Financial statements collection failed: {e}")
            return {'success': 0, 'failed': 1, 'total_records': 0}
    
    async def run_health_check(self):
        """Run health check on data pipeline"""
        logger.info("Running data pipeline health check")
        
        try:
            from ..database.database import db_manager
            
            # Check database connection
            db_healthy = await db_manager.check_connection()
            
            # Check recent data ingestion
            from sqlalchemy import select, func
            from ..database.models import DataIngestionLog
            
            async with db_manager.get_async_session() as session:
                # Check for successful runs in the last 2 days
                cutoff_date = datetime.now() - timedelta(days=2)
                
                stmt = select(func.count(DataIngestionLog.id)).where(
                    DataIngestionLog.start_time >= cutoff_date,
                    DataIngestionLog.status == 'completed'
                )
                result = await session.execute(stmt)
                recent_successful_runs = result.scalar()
            
            health_status = {
                'database_healthy': db_healthy,
                'recent_successful_runs': recent_successful_runs,
                'status': 'healthy' if db_healthy and recent_successful_runs > 0 else 'unhealthy',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Health check completed: {health_status}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'database_healthy': False,
                'recent_successful_runs': 0,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def setup_schedule(self):
        """Setup scheduled jobs"""
        logger.info("Setting up data pipeline schedule")
        
        # Market data collection after IDX close (4:30 PM WIB = 9:30 UTC)
        schedule.every().day.at(config.LQ45_UPDATE_TIME).do(
            lambda: asyncio.create_task(self.run_daily_market_data_collection())
        )
        
        # News data collection after market close (4:45 PM WIB = 9:45 UTC)
        schedule.every().day.at(config.NEWS_UPDATE_TIME).do(
            lambda: asyncio.create_task(self.run_daily_news_collection())
        )
        
        # Financial statements collection weekly on Sundays
        schedule.every().sunday.at("10:00").do(
            lambda: asyncio.create_task(self.run_weekly_financial_statements_collection())
        )
        
        # Health check every 6 hours
        schedule.every(6).hours.do(
            lambda: asyncio.create_task(self.run_health_check())
        )
        
        logger.info("Schedule setup completed")
    
    async def start_scheduler(self):
        """Start the scheduled data pipeline"""
        logger.info("Starting data pipeline scheduler")
        
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.setup_schedule()
        
        try:
            while self.running:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.running = False
        
        logger.info("Data pipeline scheduler stopped")
    
    async def run_manual_collection(self, collection_type: str = "all", days_back: int = 1):
        """Run manual data collection"""
        logger.info(f"Starting manual {collection_type} collection for {days_back} days")
        
        results = {}
        
        try:
            if collection_type in ["all", "market"]:
                results['market_data'] = await self.run_daily_market_data_collection()
            
            if collection_type in ["all", "news"]:
                results['news_data'] = await self.run_daily_news_collection()
            
            if collection_type in ["all", "financials"]:
                results['financial_statements'] = await self.run_weekly_financial_statements_collection()
            
            logger.info(f"Manual collection completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Manual collection failed: {e}")
            raise

# CLI interface
async def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AlphaGen Data Pipeline")
    parser.add_argument('command', choices=['init', 'run', 'schedule', 'health', 'collect'], 
                       help='Command to execute')
    parser.add_argument('--type', choices=['all', 'market', 'news', 'financials'], 
                       default='all', help='Type of data to collect (for collect command)')
    parser.add_argument('--days', type=int, default=1, 
                       help='Number of days back to collect data')
    
    args = parser.parse_args()
    
    pipeline = DataPipeline()
    
    try:
        if args.command == 'init':
            success = await pipeline.initialize()
            sys.exit(0 if success else 1)
            
        elif args.command == 'run':
            # Initialize first
            success = await pipeline.initialize()
            if not success:
                sys.exit(1)
            
            # Run manual collection
            await pipeline.run_manual_collection(args.type, args.days)
            
        elif args.command == 'schedule':
            # Initialize first
            success = await pipeline.initialize()
            if not success:
                sys.exit(1)
            
            # Start scheduler
            await pipeline.start_scheduler()
            
        elif args.command == 'health':
            health_status = await pipeline.run_health_check()
            print(f"Health Status: {health_status['status']}")
            if health_status['status'] == 'unhealthy':
                sys.exit(1)
            
        elif args.command == 'collect':
            # Initialize first
            success = await pipeline.initialize()
            if not success:
                sys.exit(1)
            
            # Run collection
            await pipeline.run_manual_collection(args.type, args.days)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())