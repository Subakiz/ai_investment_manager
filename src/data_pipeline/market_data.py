"""
Market data collection pipeline for Indonesian stocks
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from sqlalchemy import select, insert, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..database.database import db_manager
from ..database.models import Stock, StockPrice, FinancialStatement, DataIngestionLog
from ..utils.logger import get_pipeline_logger
from .lq45_stocks import LQ45_STOCKS, get_lq45_symbols
from ..config.settings import config

logger = get_pipeline_logger()

class MarketDataCollector:
    """Collect and store market data for Indonesian stocks"""
    
    def __init__(self):
        self.symbols = get_lq45_symbols()
        self.session_id = None
    
    async def initialize_stocks(self):
        """Initialize stocks table with LQ45 companies"""
        logger.info("Initializing stocks table with LQ45 companies")
        
        async with db_manager.get_async_session() as session:
            for symbol, company_name in LQ45_STOCKS:
                # Check if stock already exists
                stmt = select(Stock).where(Stock.symbol == symbol)
                result = await session.execute(stmt)
                existing_stock = result.scalar_one_or_none()
                
                if not existing_stock:
                    # Create new stock record
                    stock = Stock(
                        symbol=symbol,
                        company_name=company_name,
                        is_lq45=True,
                        currency='IDR'
                    )
                    session.add(stock)
                    logger.info(f"Added new stock: {symbol} - {company_name}")
                else:
                    # Update existing stock to ensure it's marked as LQ45
                    existing_stock.is_lq45 = True
                    existing_stock.company_name = company_name
                    logger.debug(f"Updated existing stock: {symbol}")
            
            await session.commit()
        
        logger.info("Stocks table initialization completed")
    
    async def collect_daily_prices(self, days_back: int = 1) -> Dict[str, int]:
        """Collect daily price data for all LQ45 stocks"""
        start_time = datetime.now()
        self.session_id = await self._log_start('market_data')
        
        try:
            logger.info(f"Starting daily price collection for {len(self.symbols)} stocks")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back + 5)  # Extra days to handle weekends
            
            results = {
                'success': 0,
                'failed': 0,
                'total_records': 0
            }
            
            async with db_manager.get_async_session() as session:
                for symbol in self.symbols:
                    try:
                        # Get stock ID
                        stmt = select(Stock).where(Stock.symbol == symbol)
                        result = await session.execute(stmt)
                        stock = result.scalar_one_or_none()
                        
                        if not stock:
                            logger.warning(f"Stock {symbol} not found in database, skipping")
                            results['failed'] += 1
                            continue
                        
                        # Fetch data from Yahoo Finance
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(
                            start=start_date.strftime('%Y-%m-%d'),
                            end=end_date.strftime('%Y-%m-%d')
                        )
                        
                        if hist.empty:
                            logger.warning(f"No data available for {symbol}")
                            results['failed'] += 1
                            continue
                        
                        # Process each day's data
                        records_inserted = 0
                        for date, row in hist.iterrows():
                            try:
                                # Check if record already exists
                                check_stmt = select(StockPrice).where(
                                    StockPrice.stock_id == stock.id,
                                    StockPrice.trade_date == date.date()
                                )
                                existing = await session.execute(check_stmt)
                                if existing.scalar_one_or_none():
                                    continue  # Skip existing records
                                
                                # Insert new price record
                                price_data = StockPrice(
                                    stock_id=stock.id,
                                    trade_date=date.date(),
                                    open_price=float(row['Open']),
                                    high_price=float(row['High']),
                                    low_price=float(row['Low']),
                                    close_price=float(row['Close']),
                                    volume=int(row['Volume']),
                                    adjusted_close=float(row['Close'])  # Yahoo Finance already provides adjusted close
                                )
                                session.add(price_data)
                                records_inserted += 1
                                
                            except Exception as e:
                                logger.error(f"Error processing price data for {symbol} on {date}: {e}")
                                continue
                        
                        if records_inserted > 0:
                            await session.commit()
                            logger.info(f"Inserted {records_inserted} price records for {symbol}")
                            results['total_records'] += records_inserted
                        
                        results['success'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error collecting data for {symbol}: {e}")
                        results['failed'] += 1
                        continue
            
            # Log completion
            await self._log_completion(self.session_id, results['total_records'])
            logger.info(f"Market data collection completed. Success: {results['success']}, Failed: {results['failed']}, Total records: {results['total_records']}")
            
            return results
            
        except Exception as e:
            await self._log_error(self.session_id, str(e))
            logger.error(f"Market data collection failed: {e}")
            raise
    
    async def collect_financial_statements(self, symbols: Optional[List[str]] = None) -> Dict[str, int]:
        """Collect financial statement data for stocks"""
        if symbols is None:
            symbols = self.symbols
        
        start_time = datetime.now()
        session_id = await self._log_start('financial_statements')
        
        try:
            logger.info(f"Starting financial statements collection for {len(symbols)} stocks")
            
            results = {
                'success': 0,
                'failed': 0,
                'total_records': 0
            }
            
            async with db_manager.get_async_session() as session:
                for symbol in symbols:
                    try:
                        # Get stock ID
                        stmt = select(Stock).where(Stock.symbol == symbol)
                        result = await session.execute(stmt)
                        stock = result.scalar_one_or_none()
                        
                        if not stock:
                            logger.warning(f"Stock {symbol} not found in database, skipping")
                            results['failed'] += 1
                            continue
                        
                        # Fetch financial data from Yahoo Finance
                        ticker = yf.Ticker(symbol)
                        
                        # Get quarterly and annual financials
                        for statement_type, financials in [
                            ('quarterly', ticker.quarterly_financials),
                            ('annual', ticker.financials)
                        ]:
                            if financials.empty:
                                continue
                                
                            for period, data in financials.items():
                                try:
                                    # Extract key financial metrics
                                    period_date = period.date() if hasattr(period, 'date') else period
                                    
                                    # Check if record already exists
                                    check_stmt = select(FinancialStatement).where(
                                        FinancialStatement.stock_id == stock.id,
                                        FinancialStatement.statement_type == statement_type,
                                        FinancialStatement.period_end == period_date
                                    )
                                    existing = await session.execute(check_stmt)
                                    if existing.scalar_one_or_none():
                                        continue
                                    
                                    # Create financial statement record
                                    financial_stmt = FinancialStatement(
                                        stock_id=stock.id,
                                        statement_type=statement_type,
                                        period_end=period_date,
                                        fiscal_year=period_date.year,
                                        fiscal_quarter=((period_date.month - 1) // 3) + 1 if statement_type == 'quarterly' else None,
                                        # Extract available financial data
                                        revenue=self._safe_extract_value(data, ['Total Revenue', 'Revenue']),
                                        gross_profit=self._safe_extract_value(data, ['Gross Profit']),
                                        operating_income=self._safe_extract_value(data, ['Operating Income']),
                                        net_income=self._safe_extract_value(data, ['Net Income']),
                                        ebitda=self._safe_extract_value(data, ['EBITDA']),
                                    )
                                    
                                    session.add(financial_stmt)
                                    results['total_records'] += 1
                                    
                                except Exception as e:
                                    logger.error(f"Error processing financial data for {symbol} period {period}: {e}")
                                    continue
                        
                        results['success'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error collecting financial data for {symbol}: {e}")
                        results['failed'] += 1
                        continue
                
                await session.commit()
            
            # Log completion
            await self._log_completion(session_id, results['total_records'])
            logger.info(f"Financial statements collection completed. Success: {results['success']}, Failed: {results['failed']}, Total records: {results['total_records']}")
            
            return results
            
        except Exception as e:
            await self._log_error(session_id, str(e))
            logger.error(f"Financial statements collection failed: {e}")
            raise
    
    def _safe_extract_value(self, data: pd.Series, keys: List[str]) -> Optional[float]:
        """Safely extract financial value from pandas Series"""
        for key in keys:
            if key in data.index:
                value = data[key]
                if pd.notna(value) and value != 0:
                    return float(value)
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

# CLI interface for manual data collection
async def main():
    """Main function for CLI usage"""
    import sys
    
    collector = MarketDataCollector()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            await collector.initialize_stocks()
        elif command == "prices":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await collector.collect_daily_prices(days_back=days)
        elif command == "financials":
            await collector.collect_financial_statements()
        elif command == "all":
            await collector.initialize_stocks()
            await collector.collect_daily_prices()
            await collector.collect_financial_statements()
        else:
            print("Available commands: init, prices [days], financials, all")
            sys.exit(1)
    else:
        print("Usage: python -m src.data_pipeline.market_data <command>")
        print("Commands: init, prices [days], financials, all")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())