"""
Risk analysis module for AlphaGen Investment Platform
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Stock, StockPrice
from ..database.database import db_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RiskAnalyzer:
    """Risk analysis engine for stock volatility and risk scoring"""
    
    def __init__(self):
        self.logger = logger
    
    async def calculate_volatility_score(self, symbol: str, days: int = 30) -> Dict:
        """
        Calculate the volatility score for a stock symbol
        
        Args:
            symbol: Stock symbol to analyze
            days: Number of days to look back for volatility calculation
            
        Returns:
            Dict containing volatility metrics and risk score
        """
        try:
            async with db_manager.get_async_session() as db:
                # Find the stock
                stock_query = select(Stock).where(Stock.symbol == symbol.upper())
                stock_result = await db.execute(stock_query)
                stock = stock_result.scalar_one_or_none()
                
                if not stock:
                    raise ValueError(f"Stock with symbol {symbol} not found")
                
                # Get historical price data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days + 1)  # Extra day for returns calculation
                
                price_query = (
                    select(StockPrice)
                    .where(
                        and_(
                            StockPrice.stock_id == stock.id,
                            StockPrice.trade_date >= start_date,
                            StockPrice.trade_date <= end_date
                        )
                    )
                    .order_by(StockPrice.trade_date)
                )
                
                price_result = await db.execute(price_query)
                prices = price_result.scalars().all()
                
                if len(prices) < 2:
                    raise ValueError(f"Insufficient price data for {symbol}")
                
                # Convert to pandas DataFrame for analysis
                price_data = pd.DataFrame([
                    {
                        'date': price.trade_date,
                        'close': float(price.close_price),
                        'high': float(price.high_price),
                        'low': float(price.low_price),
                        'volume': price.volume
                    }
                    for price in prices
                ])
                
                # Calculate daily returns
                price_data['daily_return'] = price_data['close'].pct_change()
                
                # Remove NaN values
                returns = price_data['daily_return'].dropna()
                
                if len(returns) < 2:
                    raise ValueError(f"Insufficient return data for {symbol}")
                
                # Calculate volatility metrics
                volatility_30d = returns.std() * np.sqrt(252)  # Annualized volatility
                mean_return = returns.mean() * 252  # Annualized return
                
                # Calculate additional risk metrics
                max_drawdown = self._calculate_max_drawdown(price_data['close'])
                var_95 = np.percentile(returns, 5)  # Value at Risk (95% confidence)
                
                # Calculate normalized risk score (0-100, higher = riskier)
                risk_score = self._normalize_volatility_to_score(volatility_30d)
                
                # Determine risk level
                risk_level = self._categorize_risk_level(risk_score)
                
                # Calculate beta (if we have market data)
                beta = await self._calculate_beta(stock.id, days, db)
                
                return {
                    'stock_symbol': symbol,
                    'analysis_date': end_date,
                    'volatility_30d': volatility_30d,
                    'annualized_return': mean_return,
                    'risk_score': risk_score,
                    'risk_level': risk_level,
                    'max_drawdown': max_drawdown,
                    'var_95': var_95,
                    'beta': beta,
                    'data_points': len(returns)
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating volatility score for {symbol}: {e}")
            raise
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _normalize_volatility_to_score(self, volatility: float) -> float:
        """
        Normalize volatility to a 0-100 risk score
        
        Based on typical Indonesian stock market volatility ranges:
        - Low risk: 0-20% volatility -> 0-30 score
        - Medium risk: 20-40% volatility -> 30-70 score  
        - High risk: 40%+ volatility -> 70-100 score
        """
        if volatility <= 0.20:  # 20% volatility
            return min(30, volatility * 150)  # Scale to 0-30
        elif volatility <= 0.40:  # 40% volatility
            return 30 + ((volatility - 0.20) * 200)  # Scale to 30-70
        else:
            return min(100, 70 + ((volatility - 0.40) * 75))  # Scale to 70-100
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk score into LOW, MEDIUM, HIGH"""
        if risk_score <= 30:
            return "LOW"
        elif risk_score <= 70:
            return "MEDIUM"
        else:
            return "HIGH"
    
    async def _calculate_beta(self, stock_id: int, days: int, db: AsyncSession) -> Optional[float]:
        """
        Calculate beta against market index (simplified)
        For a complete implementation, you would need market index data
        """
        try:
            # This is a simplified beta calculation
            # In a real implementation, you would:
            # 1. Get market index data (e.g., IDX Composite)
            # 2. Calculate correlation between stock and market returns
            # 3. Return beta = correlation * (stock_volatility / market_volatility)
            
            # For now, return None to indicate beta is not available
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating beta for stock_id {stock_id}: {e}")
            return None
    
    async def calculate_portfolio_risk(self, portfolio_weights: Dict[str, float]) -> Dict:
        """
        Calculate portfolio risk metrics given stock weights
        
        Args:
            portfolio_weights: Dict of {symbol: weight} where weights sum to 1.0
            
        Returns:
            Dict containing portfolio risk metrics
        """
        try:
            if abs(sum(portfolio_weights.values()) - 1.0) > 0.01:
                raise ValueError("Portfolio weights must sum to 1.0")
            
            # Get individual stock risk metrics
            stock_risks = {}
            for symbol in portfolio_weights.keys():
                stock_risks[symbol] = await self.calculate_volatility_score(symbol)
            
            # Calculate weighted portfolio volatility (simplified)
            portfolio_volatility = 0.0
            for symbol, weight in portfolio_weights.items():
                portfolio_volatility += (weight ** 2) * (stock_risks[symbol]['volatility_30d'] ** 2)
            
            portfolio_volatility = np.sqrt(portfolio_volatility)
            
            # Calculate weighted risk score
            portfolio_risk_score = sum(
                weight * stock_risks[symbol]['risk_score'] 
                for symbol, weight in portfolio_weights.items()
            )
            
            return {
                'portfolio_volatility': portfolio_volatility,
                'portfolio_risk_score': portfolio_risk_score,
                'portfolio_risk_level': self._categorize_risk_level(portfolio_risk_score),
                'constituent_risks': stock_risks,
                'analysis_date': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio risk: {e}")
            raise


# Global instance
risk_analyzer = RiskAnalyzer()


async def calculate_volatility_score(symbol: str, days: int = 30) -> Dict:
    """Convenience function for volatility score calculation"""
    return await risk_analyzer.calculate_volatility_score(symbol, days)


async def calculate_portfolio_risk(portfolio_weights: Dict[str, float]) -> Dict:
    """Convenience function for portfolio risk calculation"""
    return await risk_analyzer.calculate_portfolio_risk(portfolio_weights)