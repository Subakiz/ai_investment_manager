"""
Quantitative Analysis Engine for AlphaGen Investment Platform

This module implements quantitative analysis functions including:
- Data fetching from PostgreSQL
- Valuation metrics calculation (P/E, P/B ratios)
- Technical indicators (RSI, moving averages, volume trends)
- Scoring and normalization system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import db_manager
from ..database.models import Stock, StockPrice, FinancialStatement, QuantitativeScores
from ..utils.logger import get_logger

logger = get_logger(__name__)

class QuantitativeAnalyzer:
    """Main class for quantitative analysis of Indonesian stocks"""
    
    def __init__(self):
        self.logger = logger
    
    async def fetch_latest_market_data(self, symbol: str = None) -> pd.DataFrame:
        """
        Fetch latest stock prices and financial data from PostgreSQL
        
        Args:
            symbol: Optional stock symbol to filter, if None returns all LQ45 stocks
            
        Returns:
            DataFrame with latest market data
        """
        async with db_manager.get_async_session() as session:
            # Base query for stocks and their latest prices
            query = (
                select(
                    Stock.symbol,
                    Stock.company_name,
                    Stock.sector,
                    StockPrice.trade_date,
                    StockPrice.close_price,
                    StockPrice.volume,
                    StockPrice.open_price,
                    StockPrice.high_price,
                    StockPrice.low_price
                )
                .join(StockPrice, Stock.id == StockPrice.stock_id)
                .where(Stock.is_lq45 == True)
                .order_by(Stock.symbol, desc(StockPrice.trade_date))
            )
            
            if symbol:
                query = query.where(Stock.symbol == symbol)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return pd.DataFrame()
            
            # Convert to DataFrame and get only latest price per stock
            df = pd.DataFrame(rows, columns=[
                'symbol', 'company_name', 'sector', 'trade_date', 
                'close_price', 'volume', 'open_price', 'high_price', 'low_price'
            ])
            
            # Get latest date per symbol
            latest_df = df.loc[df.groupby('symbol')['trade_date'].idxmax()]
            
            self.logger.info(f"Fetched latest market data for {len(latest_df)} stocks")
            return latest_df
    
    async def fetch_historical_data(self, symbol: str, days: int = 252) -> pd.DataFrame:
        """
        Get historical price data for trend analysis
        
        Args:
            symbol: Stock symbol (e.g., 'BBCA.JK')
            days: Number of days to look back (default 252 for 1 year)
            
        Returns:
            DataFrame with historical price data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        async with db_manager.get_async_session() as session:
            query = (
                select(
                    StockPrice.trade_date,
                    StockPrice.open_price,
                    StockPrice.high_price,
                    StockPrice.low_price,
                    StockPrice.close_price,
                    StockPrice.volume
                )
                .join(Stock, Stock.id == StockPrice.stock_id)
                .where(
                    and_(
                        Stock.symbol == symbol,
                        StockPrice.trade_date >= cutoff_date
                    )
                )
                .order_by(StockPrice.trade_date)
            )
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                self.logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=[
                'trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
            ])
            
            # Convert to numeric
            numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.set_index('trade_date').sort_index()
            
            self.logger.debug(f"Fetched {len(df)} days of historical data for {symbol}")
            return df
    
    async def get_latest_financial_data(self, symbol: str) -> Optional[Dict]:
        """Get latest financial statement data for a stock"""
        async with db_manager.get_async_session() as session:
            query = (
                select(FinancialStatement)
                .join(Stock, Stock.id == FinancialStatement.stock_id)
                .where(Stock.symbol == symbol)
                .order_by(desc(FinancialStatement.period_end))
                .limit(1)
            )
            
            result = await session.execute(query)
            financial = result.scalar_one_or_none()
            
            if financial:
                return {
                    'revenue': float(financial.revenue or 0),
                    'net_income': float(financial.net_income or 0),
                    'total_assets': float(financial.total_assets or 0),
                    'total_equity': float(financial.total_equity or 0),
                    'eps': float(financial.eps or 0),
                    'pe_ratio': float(financial.pe_ratio or 0),
                    'pb_ratio': float(financial.pb_ratio or 0),
                    'roe': float(financial.roe or 0),
                    'period_end': financial.period_end
                }
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate technical indicators for a stock
        
        Args:
            df: DataFrame with OHLCV data indexed by date
            
        Returns:
            Dictionary with technical indicators
        """
        if df.empty or len(df) < 50:
            return {}
        
        indicators = {}
        
        # RSI calculation
        delta = df['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        indicators['rsi'] = float(rsi.iloc[-1]) if not rsi.empty else 50.0
        
        # Moving averages
        if len(df) >= 50:
            indicators['ma_50'] = float(df['close_price'].rolling(50).mean().iloc[-1])
        if len(df) >= 200:
            indicators['ma_200'] = float(df['close_price'].rolling(200).mean().iloc[-1])
        
        # Current price
        indicators['current_price'] = float(df['close_price'].iloc[-1])
        
        # Moving average signals
        if 'ma_50' in indicators and 'ma_200' in indicators:
            if indicators['ma_50'] > indicators['ma_200']:
                indicators['ma_signal'] = 'bullish'
            elif indicators['ma_50'] < indicators['ma_200']:
                indicators['ma_signal'] = 'bearish'
            else:
                indicators['ma_signal'] = 'neutral'
        else:
            indicators['ma_signal'] = 'neutral'
        
        # Volume trend (last 20 days vs previous 20 days)
        if len(df) >= 40:
            recent_volume = df['volume'].tail(20).mean()
            previous_volume = df['volume'].tail(40).head(20).mean()
            
            if recent_volume > previous_volume * 1.1:
                indicators['volume_trend'] = 'increasing'
            elif recent_volume < previous_volume * 0.9:
                indicators['volume_trend'] = 'decreasing'
            else:
                indicators['volume_trend'] = 'stable'
        else:
            indicators['volume_trend'] = 'stable'
        
        return indicators
    
    def calculate_relative_valuation(self, symbol: str, financial_data: Dict, current_price: float) -> Dict[str, float]:
        """
        Calculate relative valuation metrics
        
        Args:
            symbol: Stock symbol
            financial_data: Financial statement data
            current_price: Current stock price
            
        Returns:
            Dictionary with valuation scores
        """
        valuation = {}
        
        # Calculate current P/E ratio if EPS available
        eps = financial_data.get('eps', 0)
        if eps > 0:
            current_pe = current_price / eps
            valuation['pe_ratio'] = current_pe
            
            # Simple P/E scoring (lower is better, typical range 5-30)
            if current_pe < 10:
                valuation['pe_score'] = 90.0
            elif current_pe < 15:
                valuation['pe_score'] = 75.0
            elif current_pe < 20:
                valuation['pe_score'] = 60.0
            elif current_pe < 25:
                valuation['pe_score'] = 40.0
            else:
                valuation['pe_score'] = 20.0
        else:
            valuation['pe_ratio'] = 0
            valuation['pe_score'] = 50.0  # Neutral score
        
        # Calculate P/B ratio if book value available
        total_equity = financial_data.get('total_equity', 0)
        if total_equity > 0:
            # Estimate shares outstanding (simplified)
            market_cap = current_price * 1000000  # Rough estimation
            book_value_per_share = total_equity / 1000000  # Simplified
            
            if book_value_per_share > 0:
                current_pb = current_price / book_value_per_share
                valuation['pb_ratio'] = current_pb
                
                # Simple P/B scoring (lower is better, typical range 0.5-3)
                if current_pb < 1:
                    valuation['pb_score'] = 90.0
                elif current_pb < 1.5:
                    valuation['pb_score'] = 75.0
                elif current_pb < 2:
                    valuation['pb_score'] = 60.0
                elif current_pb < 3:
                    valuation['pb_score'] = 40.0
                else:
                    valuation['pb_score'] = 20.0
            else:
                valuation['pb_ratio'] = 0
                valuation['pb_score'] = 50.0
        else:
            valuation['pb_ratio'] = 0
            valuation['pb_score'] = 50.0
        
        return valuation
    
    def calculate_technical_scores(self, indicators: Dict[str, float]) -> Dict[str, float]:
        """
        Convert technical indicators to 0-100 scores
        
        Args:
            indicators: Technical indicators dictionary
            
        Returns:
            Dictionary with technical scores
        """
        scores = {}
        
        # RSI scoring (30-70 is good range, outside is oversold/overbought)
        rsi = indicators.get('rsi', 50)
        if 30 <= rsi <= 70:
            scores['rsi_score'] = 80.0  # Good range
        elif 20 <= rsi < 30 or 70 < rsi <= 80:
            scores['rsi_score'] = 60.0  # Moderate
        else:
            scores['rsi_score'] = 30.0  # Extreme levels
        
        # Moving average scoring
        ma_signal = indicators.get('ma_signal', 'neutral')
        current_price = indicators.get('current_price', 0)
        ma_50 = indicators.get('ma_50', current_price)
        ma_200 = indicators.get('ma_200', current_price)
        
        if ma_signal == 'bullish':
            scores['ma_score'] = 75.0
        elif ma_signal == 'bearish':
            scores['ma_score'] = 25.0
        else:
            scores['ma_score'] = 50.0
        
        # Price position relative to MAs
        if current_price > ma_50 and current_price > ma_200:
            scores['ma_score'] = min(scores['ma_score'] + 15, 100)
        elif current_price < ma_50 and current_price < ma_200:
            scores['ma_score'] = max(scores['ma_score'] - 15, 0)
        
        # Volume trend scoring
        volume_trend = indicators.get('volume_trend', 'stable')
        if volume_trend == 'increasing':
            scores['volume_score'] = 75.0
        elif volume_trend == 'decreasing':
            scores['volume_score'] = 40.0
        else:
            scores['volume_score'] = 60.0
        
        return scores
    
    def calculate_composite_score(self, valuation_scores: Dict, technical_scores: Dict) -> Dict[str, float]:
        """
        Calculate weighted composite quantitative score
        
        Args:
            valuation_scores: Valuation metrics scores
            technical_scores: Technical analysis scores
            
        Returns:
            Dictionary with composite scores
        """
        # Weights for different components
        weights = {
            'valuation': 0.4,
            'technical': 0.6
        }
        
        # Calculate component scores
        pe_score = valuation_scores.get('pe_score', 50.0)
        pb_score = valuation_scores.get('pb_score', 50.0)
        valuation_composite = (pe_score + pb_score) / 2
        
        rsi_score = technical_scores.get('rsi_score', 50.0)
        ma_score = technical_scores.get('ma_score', 50.0)
        volume_score = technical_scores.get('volume_score', 50.0)
        technical_composite = (rsi_score + ma_score + volume_score) / 3
        
        # Final composite score
        composite_score = (
            valuation_composite * weights['valuation'] +
            technical_composite * weights['technical']
        )
        
        return {
            'valuation_score': round(valuation_composite, 2),
            'technical_score': round(technical_composite, 2),
            'composite_score': round(composite_score, 2)
        }
    
    async def analyze_single_stock(self, symbol: str) -> Dict:
        """
        Run complete quantitative analysis for a single stock
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dictionary with complete analysis results
        """
        try:
            self.logger.info(f"Starting quantitative analysis for {symbol}")
            
            # Fetch historical data
            historical_data = await self.fetch_historical_data(symbol, days=252)
            if historical_data.empty:
                self.logger.warning(f"No historical data for {symbol}")
                return {}
            
            # Get financial data
            financial_data = await self.get_latest_financial_data(symbol)
            if not financial_data:
                self.logger.warning(f"No financial data for {symbol}")
                financial_data = {}
            
            # Calculate technical indicators
            technical_indicators = self.calculate_technical_indicators(historical_data)
            
            # Calculate valuation metrics
            current_price = technical_indicators.get('current_price', 0)
            valuation_metrics = self.calculate_relative_valuation(symbol, financial_data, current_price)
            
            # Calculate scores
            technical_scores = self.calculate_technical_scores(technical_indicators)
            composite_scores = self.calculate_composite_score(valuation_metrics, technical_scores)
            
            # Combine all results
            analysis_result = {
                'symbol': symbol,
                'analysis_date': datetime.now(),
                'current_price': current_price,
                **valuation_metrics,
                **technical_indicators,
                **technical_scores,
                **composite_scores
            }
            
            self.logger.info(f"Completed quantitative analysis for {symbol}: score={composite_scores.get('composite_score', 0)}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {}
    
    async def save_quantitative_scores(self, analysis_results: List[Dict]) -> int:
        """
        Save quantitative analysis results to database
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            Number of records saved
        """
        if not analysis_results:
            return 0
        
        saved_count = 0
        
        async with db_manager.get_async_session() as session:
            for result in analysis_results:
                if not result:
                    continue
                
                try:
                    # Get stock_id
                    stock_query = select(Stock.id).where(Stock.symbol == result['symbol'])
                    stock_result = await session.execute(stock_query)
                    stock_id = stock_result.scalar_one_or_none()
                    
                    if not stock_id:
                        self.logger.warning(f"Stock not found: {result['symbol']}")
                        continue
                    
                    # Create quantitative score record
                    score_record = QuantitativeScores(
                        stock_id=stock_id,
                        analysis_date=result['analysis_date'],
                        pe_ratio=result.get('pe_ratio'),
                        pb_ratio=result.get('pb_ratio'),
                        pe_relative_score=result.get('pe_score'),
                        pb_relative_score=result.get('pb_score'),
                        rsi=result.get('rsi'),
                        rsi_score=result.get('rsi_score'),
                        ma_50=result.get('ma_50'),
                        ma_200=result.get('ma_200'),
                        ma_signal=result.get('ma_signal'),
                        ma_score=result.get('ma_score'),
                        volume_trend=result.get('volume_trend'),
                        volume_score=result.get('volume_score'),
                        valuation_score=result.get('valuation_score'),
                        technical_score=result.get('technical_score'),
                        composite_score=result.get('composite_score')
                    )
                    
                    session.add(score_record)
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error saving quantitative score for {result.get('symbol', 'unknown')}: {e}")
                    continue
            
            await session.commit()
        
        self.logger.info(f"Saved {saved_count} quantitative analysis records")
        return saved_count
    
    async def run_quantitative_analysis(self, symbols: List[str] = None) -> Dict[str, int]:
        """
        Main orchestration function for quantitative analysis
        
        Args:
            symbols: Optional list of symbols to analyze, if None analyzes all LQ45
            
        Returns:
            Dictionary with analysis results summary
        """
        self.logger.info("Starting quantitative analysis pipeline")
        
        try:
            # Get symbols to analyze
            if not symbols:
                # Get all LQ45 symbols
                async with db_manager.get_async_session() as session:
                    query = select(Stock.symbol).where(Stock.is_lq45 == True)
                    result = await session.execute(query)
                    symbols = [row[0] for row in result.fetchall()]
            
            if not symbols:
                self.logger.warning("No symbols found for analysis")
                return {'analyzed': 0, 'saved': 0, 'errors': 0}
            
            self.logger.info(f"Analyzing {len(symbols)} stocks")
            
            # Analyze each stock
            analysis_results = []
            error_count = 0
            
            for symbol in symbols:
                try:
                    result = await self.analyze_single_stock(symbol)
                    if result:
                        analysis_results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to analyze {symbol}: {e}")
                    error_count += 1
            
            # Save results
            saved_count = await self.save_quantitative_scores(analysis_results)
            
            summary = {
                'analyzed': len(analysis_results),
                'saved': saved_count,
                'errors': error_count,
                'total_symbols': len(symbols)
            }
            
            self.logger.info(f"Quantitative analysis completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Quantitative analysis pipeline failed: {e}")
            return {'analyzed': 0, 'saved': 0, 'errors': 1}

# CLI interface
async def main():
    """Main function for CLI usage"""
    import sys
    
    analyzer = QuantitativeAnalyzer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "analyze":
            # Run analysis for all stocks
            result = await analyzer.run_quantitative_analysis()
            print(f"Analysis completed: {result}")
            
        elif command == "analyze-symbol":
            if len(sys.argv) > 2:
                symbol = sys.argv[2]
                result = await analyzer.analyze_single_stock(symbol)
                print(f"Analysis for {symbol}: {result}")
            else:
                print("Usage: python -m src.analysis.quantitative analyze-symbol <SYMBOL>")
                
        else:
            print("Available commands: analyze, analyze-symbol <SYMBOL>")
            sys.exit(1)
    else:
        print("Usage: python -m src.analysis.quantitative <command>")
        print("Commands: analyze, analyze-symbol <SYMBOL>")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())