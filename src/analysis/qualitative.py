"""
Qualitative Analysis Engine for AlphaGen Investment Platform

This module implements AI-powered sentiment analysis using Google Gemini 2.5 Pro including:
- Gemini API integration with structured prompts
- News article sentiment analysis 
- Batch processing of articles
- Theme extraction and company-specific sentiment aggregation
- Structured JSON output processing
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import select, and_, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..database.database import db_manager
from ..database.models import NewsArticle, Stock, SentimentAnalysis, NewsStockMention
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class QualitativeAnalyzer:
    """Main class for qualitative analysis using Gemini AI"""
    
    def __init__(self):
        self.logger = logger
        self.model = None
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.max_retries = 3
        
    def initialize_gemini_client(self) -> bool:
        """
        Initialize Gemini client with API key from environment
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not config.GEMINI_API_KEY:
                self.logger.error("GEMINI_API_KEY not found in configuration")
                return False
            
            # Configure Gemini
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Initialize model with safety settings for financial content
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                safety_settings=safety_settings
            )
            
            self.logger.info("Gemini client initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            return False
    
    def create_sentiment_prompt(self, article_text: str, company_name: str = "", symbol: str = "") -> str:
        """
        Create engineered prompt for structured sentiment analysis
        
        Args:
            article_text: The news article content
            company_name: Company name if known
            symbol: Stock symbol if known
            
        Returns:
            Structured prompt for Gemini
        """
        company_info = ""
        if company_name and symbol:
            company_info = f" about {company_name} ({symbol})"
        elif company_name:
            company_info = f" about {company_name}"
        elif symbol:
            company_info = f" about {symbol}"
        
        prompt = f"""Analyze this Indonesian financial news article{company_info} and return ONLY a valid JSON object with these exact keys:

REQUIRED RESPONSE FORMAT (JSON only, no additional text):
{{
  "sentiment_score": <float from -1.0 (very negative) to 1.0 (very positive)>,
  "confidence": <float from 0.0 to 1.0 indicating analysis confidence>,
  "themes": [<array of 1-3 key themes, e.g., ["earnings growth", "digital transformation"]>],
  "summary": "<single sentence summary, max 100 characters>",
  "relevance": <float from 0.0 to 1.0 indicating relevance to stock price movement>
}}

ANALYSIS GUIDELINES:
- Focus on financial impact and business implications
- Consider both short-term and long-term effects on company value
- For Indonesian content, understand local business context
- Themes should be concise business/financial concepts
- Summary should capture the main investment-relevant point

ARTICLE TEXT:
{article_text[:2000]}"""  # Limit to avoid token limits
        
        return prompt
    
    async def analyze_article_sentiment(self, article_text: str, symbol: str = "", company_name: str = "") -> Optional[Dict]:
        """
        Analyze sentiment of a single article using Gemini
        
        Args:
            article_text: The article content to analyze
            symbol: Optional stock symbol
            company_name: Optional company name
            
        Returns:
            Dictionary with sentiment analysis results or None if failed
        """
        if not self.model:
            if not self.initialize_gemini_client():
                return None
        
        try:
            prompt = self.create_sentiment_prompt(article_text, company_name, symbol)
            
            start_time = time.time()
            
            # Generate content with retry logic
            for attempt in range(self.max_retries):
                try:
                    response = self.model.generate_content(prompt)
                    
                    if response and response.text:
                        # Try to parse JSON response
                        try:
                            # Clean the response text
                            response_text = response.text.strip()
                            
                            # Remove markdown code blocks if present
                            if response_text.startswith('```json'):
                                response_text = response_text[7:]
                            if response_text.startswith('```'):
                                response_text = response_text[3:]
                            if response_text.endswith('```'):
                                response_text = response_text[:-3]
                            
                            response_text = response_text.strip()
                            
                            # Parse JSON
                            result = json.loads(response_text)
                            
                            # Validate required fields
                            required_fields = ['sentiment_score', 'confidence', 'themes', 'summary', 'relevance']
                            if all(field in result for field in required_fields):
                                # Add processing metadata
                                result['processing_time_ms'] = int((time.time() - start_time) * 1000)
                                result['model_used'] = 'gemini-1.5-pro'
                                
                                # Validate and clamp values
                                result['sentiment_score'] = max(-1.0, min(1.0, float(result['sentiment_score'])))
                                result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
                                result['relevance'] = max(0.0, min(1.0, float(result['relevance'])))
                                
                                # Ensure themes is a list
                                if not isinstance(result['themes'], list):
                                    result['themes'] = [str(result['themes'])]
                                
                                # Ensure summary is a string and limit length
                                result['summary'] = str(result['summary'])[:100]
                                
                                self.logger.debug(f"Successfully analyzed sentiment: {result['sentiment_score']:.2f}")
                                return result
                            else:
                                self.logger.warning(f"Missing required fields in response: {result}")
                        
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}): {e}")
                            self.logger.debug(f"Raw response: {response.text[:200]}...")
                            
                            if attempt == self.max_retries - 1:
                                # Return basic analysis on final failure
                                return {
                                    'sentiment_score': 0.0,
                                    'confidence': 0.3,
                                    'themes': ['analysis_failed'],
                                    'summary': 'Failed to parse AI response',
                                    'relevance': 0.5,
                                    'processing_time_ms': int((time.time() - start_time) * 1000),
                                    'model_used': 'gemini-1.5-pro'
                                }
                    
                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    self.logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.rate_limit_delay * (attempt + 1))
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing article sentiment: {e}")
            return None
    
    async def fetch_unprocessed_articles(self, hours_back: int = 24, limit: int = 100) -> List[Dict]:
        """
        Fetch news articles that haven't been processed for sentiment analysis
        
        Args:
            hours_back: How many hours back to look for articles
            limit: Maximum number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        async with db_manager.get_async_session() as session:
            query = (
                select(NewsArticle)
                .where(
                    and_(
                        NewsArticle.published_at >= cutoff_time,
                        NewsArticle.processed_at.is_(None)  # Not yet processed
                    )
                )
                .order_by(desc(NewsArticle.published_at))
                .limit(limit)
            )
            
            result = await session.execute(query)
            articles = result.scalars().all()
            
            article_list = []
            for article in articles:
                article_dict = {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content or article.summary or article.title,
                    'url': article.url,
                    'source': article.source,
                    'published_at': article.published_at
                }
                article_list.append(article_dict)
            
            self.logger.info(f"Fetched {len(article_list)} unprocessed articles")
            return article_list
    
    async def batch_analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Efficiently batch process multiple articles for sentiment analysis
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of analysis results
        """
        if not articles:
            return []
        
        self.logger.info(f"Starting batch analysis of {len(articles)} articles")
        
        results = []
        processed = 0
        errors = 0
        
        for article in articles:
            try:
                # Prepare article text
                article_text = article.get('content', '') or article.get('title', '')
                if not article_text.strip():
                    self.logger.warning(f"Empty article content for ID {article['id']}")
                    continue
                
                # Analyze sentiment
                sentiment_result = await self.analyze_article_sentiment(article_text)
                
                if sentiment_result:
                    sentiment_result['article_id'] = article['id']
                    results.append(sentiment_result)
                    processed += 1
                else:
                    errors += 1
                    self.logger.warning(f"Failed to analyze article ID {article['id']}")
                
                # Progress logging
                if processed % 10 == 0:
                    self.logger.info(f"Processed {processed}/{len(articles)} articles")
                
            except Exception as e:
                self.logger.error(f"Error processing article ID {article.get('id', 'unknown')}: {e}")
                errors += 1
                continue
        
        self.logger.info(f"Batch analysis completed: {processed} successful, {errors} errors")
        return results
    
    async def save_sentiment_analysis(self, analysis_results: List[Dict]) -> int:
        """
        Save sentiment analysis results to database
        
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
                try:
                    article_id = result['article_id']
                    
                    # Create sentiment analysis record
                    sentiment_record = SentimentAnalysis(
                        news_article_id=article_id,
                        sentiment_score=result['sentiment_score'],
                        confidence=result['confidence'],
                        themes=json.dumps(result['themes']),
                        summary=result['summary'],
                        relevance=result['relevance'],
                        model_used=result['model_used'],
                        processing_time_ms=result['processing_time_ms']
                    )
                    
                    session.add(sentiment_record)
                    
                    # Update the news article with processed sentiment
                    await session.execute(
                        update(NewsArticle)
                        .where(NewsArticle.id == article_id)
                        .values(
                            sentiment_score=result['sentiment_score'],
                            confidence=result['confidence'],
                            themes=json.dumps(result['themes']),
                            ai_summary=result['summary'],
                            processed_at=datetime.now()
                        )
                    )
                    
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error saving sentiment analysis for article {result.get('article_id', 'unknown')}: {e}")
                    continue
            
            await session.commit()
        
        self.logger.info(f"Saved {saved_count} sentiment analysis records")
        return saved_count
    
    async def extract_themes(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Extract and count key themes from analyzed articles
        
        Args:
            articles: List of articles with themes
            
        Returns:
            Dictionary with theme counts
        """
        theme_counts = {}
        
        for article in articles:
            themes = article.get('themes', [])
            if isinstance(themes, str):
                try:
                    themes = json.loads(themes)
                except:
                    themes = [themes]
            
            for theme in themes:
                if isinstance(theme, str) and theme.strip():
                    theme = theme.strip().lower()
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Sort by frequency
        sorted_themes = dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))
        
        self.logger.info(f"Extracted {len(sorted_themes)} unique themes")
        return sorted_themes
    
    async def aggregate_sentiment_by_symbol(self, hours_back: int = 24) -> Dict[str, Dict]:
        """
        Aggregate sentiment analysis by stock symbol for recent articles
        
        Args:
            hours_back: How many hours back to aggregate
            
        Returns:
            Dictionary with symbol-based sentiment aggregation
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        async with db_manager.get_async_session() as session:
            # Get articles with sentiment analysis and stock mentions
            query = (
                select(
                    Stock.symbol,
                    Stock.company_name,
                    NewsArticle.sentiment_score,
                    NewsArticle.confidence,
                    NewsArticle.themes,
                    NewsStockMention.sentiment_impact
                )
                .join(NewsStockMention, NewsStockMention.news_article_id == NewsArticle.id)
                .join(Stock, Stock.id == NewsStockMention.stock_id)
                .where(
                    and_(
                        NewsArticle.published_at >= cutoff_time,
                        NewsArticle.processed_at.is_not(None),
                        NewsArticle.sentiment_score.is_not(None)
                    )
                )
            )
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            # Aggregate by symbol
            symbol_sentiment = {}
            
            for row in rows:
                symbol = row.symbol
                if symbol not in symbol_sentiment:
                    symbol_sentiment[symbol] = {
                        'company_name': row.company_name,
                        'sentiment_scores': [],
                        'confidence_scores': [],
                        'themes': [],
                        'article_count': 0
                    }
                
                if row.sentiment_score is not None:
                    symbol_sentiment[symbol]['sentiment_scores'].append(float(row.sentiment_score))
                
                if row.confidence is not None:
                    symbol_sentiment[symbol]['confidence_scores'].append(float(row.confidence))
                
                if row.themes:
                    try:
                        themes = json.loads(row.themes)
                        if isinstance(themes, list):
                            symbol_sentiment[symbol]['themes'].extend(themes)
                    except:
                        pass
                
                symbol_sentiment[symbol]['article_count'] += 1
            
            # Calculate aggregated scores
            for symbol, data in symbol_sentiment.items():
                if data['sentiment_scores']:
                    # Weighted average by confidence
                    if data['confidence_scores'] and len(data['confidence_scores']) == len(data['sentiment_scores']):
                        weighted_sentiment = sum(s * c for s, c in zip(data['sentiment_scores'], data['confidence_scores']))
                        total_confidence = sum(data['confidence_scores'])
                        data['avg_sentiment'] = weighted_sentiment / total_confidence if total_confidence > 0 else 0.0
                    else:
                        data['avg_sentiment'] = sum(data['sentiment_scores']) / len(data['sentiment_scores'])
                    
                    data['avg_confidence'] = sum(data['confidence_scores']) / len(data['confidence_scores']) if data['confidence_scores'] else 0.0
                else:
                    data['avg_sentiment'] = 0.0
                    data['avg_confidence'] = 0.0
                
                # Clean up temporary lists
                del data['sentiment_scores']
                del data['confidence_scores']
        
        self.logger.info(f"Aggregated sentiment for {len(symbol_sentiment)} symbols")
        return symbol_sentiment
    
    async def run_qualitative_analysis(self, hours_back: int = 24) -> Dict[str, int]:
        """
        Main orchestration function for qualitative analysis
        
        Args:
            hours_back: How many hours back to process articles
            
        Returns:
            Dictionary with analysis results summary
        """
        self.logger.info("Starting qualitative analysis pipeline")
        
        try:
            # Initialize Gemini client
            if not self.initialize_gemini_client():
                return {'processed': 0, 'saved': 0, 'errors': 1}
            
            # Fetch unprocessed articles
            articles = await self.fetch_unprocessed_articles(hours_back=hours_back, limit=100)
            
            if not articles:
                self.logger.info("No unprocessed articles found")
                return {'processed': 0, 'saved': 0, 'errors': 0}
            
            # Batch analyze articles
            analysis_results = await self.batch_analyze_articles(articles)
            
            # Save results
            saved_count = await self.save_sentiment_analysis(analysis_results)
            
            # Extract themes for reporting
            themes = await self.extract_themes(analysis_results)
            top_themes = list(themes.keys())[:5]
            
            summary = {
                'processed': len(analysis_results),
                'saved': saved_count,
                'errors': len(articles) - len(analysis_results),
                'total_articles': len(articles),
                'top_themes': top_themes
            }
            
            self.logger.info(f"Qualitative analysis completed: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Qualitative analysis pipeline failed: {e}")
            return {'processed': 0, 'saved': 0, 'errors': 1}

# CLI interface
async def main():
    """Main function for CLI usage"""
    import sys
    
    analyzer = QualitativeAnalyzer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "analyze":
            # Run sentiment analysis for recent articles
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            result = await analyzer.run_qualitative_analysis(hours_back=hours)
            print(f"Qualitative analysis completed: {result}")
            
        elif command == "aggregate":
            # Show sentiment aggregation by symbol
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            aggregated = await analyzer.aggregate_sentiment_by_symbol(hours_back=hours)
            
            print(f"Sentiment aggregation (last {hours} hours):")
            for symbol, data in aggregated.items():
                print(f"{symbol}: sentiment={data['avg_sentiment']:.2f}, confidence={data['avg_confidence']:.2f}, articles={data['article_count']}")
            
        elif command == "test-article":
            # Test analysis on sample text
            if len(sys.argv) > 2:
                test_text = " ".join(sys.argv[2:])
                result = await analyzer.analyze_article_sentiment(test_text)
                print(f"Test analysis result: {result}")
            else:
                print("Usage: python -m src.analysis.qualitative test-article <TEXT>")
        
        else:
            print("Available commands: analyze [hours], aggregate [hours], test-article <TEXT>")
            sys.exit(1)
    else:
        print("Usage: python -m src.analysis.qualitative <command>")
        print("Commands: analyze [hours], aggregate [hours], test-article <TEXT>")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())