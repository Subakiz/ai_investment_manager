"""
Table components for AlphaGen Dashboard

Reusable data table components.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from ..utils.formatting import (
    format_currency, format_percentage, format_score, format_sentiment,
    format_recommendation, format_date, format_volume, truncate_text,
    get_recommendation_color, get_sentiment_color, get_score_emoji
)

def create_news_table(articles: List[Dict[str, Any]], show_sentiment: bool = True):
    """Create sortable news table with sentiment"""
    if not articles:
        st.info("No news articles available")
        return
    
    # Prepare data for table
    table_data = []
    for article in articles:
        row = {
            'Title': truncate_text(article.get('title', ''), 80),
            'Published': format_date(article.get('published_at')),
            'Summary': truncate_text(article.get('summary', ''), 100) if article.get('summary') else '-'
        }
        
        if show_sentiment:
            row['Sentiment'] = format_sentiment(article.get('sentiment_score'))
            row['Confidence'] = f"{article.get('confidence', 0):.2f}" if article.get('confidence') else '-'
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Display with custom styling
    st.subheader(f"Recent News ({len(articles)} articles)")
    
    # Add filtering options
    if show_sentiment:
        col1, col2 = st.columns(2)
        with col1:
            sentiment_filter = st.selectbox(
                "Filter by sentiment:",
                ["All", "Positive", "Negative", "Neutral"],
                key="news_sentiment_filter"
            )
        with col2:
            if st.button("Refresh News", key="refresh_news"):
                st.rerun()
    
    # Apply sentiment filter if selected
    if show_sentiment and sentiment_filter != "All":
        if sentiment_filter == "Positive":
            mask = df['Sentiment'].str.contains(r'\+', na=False)
        elif sentiment_filter == "Negative":
            mask = df['Sentiment'].str.contains(r'-', na=False)
        else:  # Neutral
            mask = df['Sentiment'].str.contains(r'0\.00', na=False)
        df = df[mask]
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Published": st.column_config.TextColumn("Published", width="small"),
            "Summary": st.column_config.TextColumn("Summary", width="large"),
            "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
            "Confidence": st.column_config.TextColumn("Confidence", width="small")
        }
    )

def create_stocks_ranking(stocks: List[Dict[str, Any]], show_scores: bool = True):
    """Create stocks ranking table"""
    if not stocks:
        st.info("No stocks data available")
        return
    
    # Prepare data for table
    table_data = []
    for i, stock in enumerate(stocks):
        row = {
            'Rank': i + 1,
            'Symbol': stock.get('symbol', ''),
            'Company': truncate_text(stock.get('company_name', ''), 40),
            'Sector': stock.get('sector', 'N/A'),
            'Recommendation': format_recommendation(stock.get('recommendation'))
        }
        
        if show_scores:
            row['Combined Score'] = format_score(stock.get('combined_score'))
            row['Quant Score'] = format_score(stock.get('quantitative_score'))
            row['Qual Score'] = format_score(stock.get('qualitative_score'))
            row['Confidence'] = stock.get('confidence', 'N/A')
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    st.subheader(f"Stock Rankings ({len(stocks)} stocks)")
    
    # Add filtering options
    col1, col2, col3 = st.columns(3)
    with col1:
        sector_filter = st.selectbox(
            "Filter by sector:",
            ["All"] + sorted(df['Sector'].unique().tolist()),
            key="stock_sector_filter"
        )
    with col2:
        recommendation_filter = st.selectbox(
            "Filter by recommendation:",
            ["All", "🚀 BUY", "⏸️ HOLD", "📉 SELL"],
            key="stock_rec_filter"
        )
    with col3:
        if st.button("Refresh Stocks", key="refresh_stocks"):
            st.rerun()
    
    # Apply filters
    filtered_df = df.copy()
    if sector_filter != "All":
        filtered_df = filtered_df[filtered_df['Sector'] == sector_filter]
    if recommendation_filter != "All":
        filtered_df = filtered_df[filtered_df['Recommendation'] == recommendation_filter]
    
    # Display table with custom styling
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Symbol": st.column_config.TextColumn("Symbol", width="small"),
            "Company": st.column_config.TextColumn("Company", width="medium"),
            "Sector": st.column_config.TextColumn("Sector", width="medium"),
            "Recommendation": st.column_config.TextColumn("Rec", width="small"),
            "Combined Score": st.column_config.TextColumn("Score", width="small"),
            "Quant Score": st.column_config.TextColumn("Quant", width="small"),
            "Qual Score": st.column_config.TextColumn("Qual", width="small"),
            "Confidence": st.column_config.TextColumn("Conf", width="small")
        }
    )

def create_themes_table(themes: List[Dict[str, Any]]):
    """Create themes occurrence ranking table"""
    if not themes:
        st.info("No themes data available")
        return
    
    # Prepare data for table
    table_data = []
    for i, theme in enumerate(themes):
        table_data.append({
            'Rank': i + 1,
            'Theme': theme.get('theme', ''),
            'Mentions': theme.get('occurrence_count', 0),
            'Avg Sentiment': format_sentiment(theme.get('avg_sentiment', 0)),
            'Related Stocks': ', '.join(theme.get('related_stocks', [])[:3])  # Show first 3 stocks
        })
    
    df = pd.DataFrame(table_data)
    
    st.subheader(f"Trending Themes ({len(themes)} themes)")
    
    # Add filtering options
    col1, col2 = st.columns(2)
    with col1:
        min_mentions = st.slider(
            "Minimum mentions:",
            min_value=1,
            max_value=max(df['Mentions']) if not df.empty else 10,
            value=2,
            key="theme_mentions_filter"
        )
    with col2:
        if st.button("Refresh Themes", key="refresh_themes"):
            st.rerun()
    
    # Apply filter
    filtered_df = df[df['Mentions'] >= min_mentions]
    
    # Display table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Theme": st.column_config.TextColumn("Theme", width="large"),
            "Mentions": st.column_config.NumberColumn("Mentions", width="small"),
            "Avg Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
            "Related Stocks": st.column_config.TextColumn("Related Stocks", width="medium")
        }
    )

def create_price_history_table(prices: List[Dict[str, Any]], symbol: str):
    """Create price history table"""
    if not prices:
        st.info("No price history available")
        return
    
    # Prepare data for table
    table_data = []
    for price in prices:
        # Calculate daily change if we have open and close
        open_price = price.get('open', 0)
        close_price = price.get('close', 0)
        change = close_price - open_price if open_price and close_price else 0
        change_pct = (change / open_price * 100) if open_price else 0
        
        table_data.append({
            'Date': format_date(price.get('date')),
            'Open': format_currency(price.get('open', 0)),
            'High': format_currency(price.get('high', 0)),
            'Low': format_currency(price.get('low', 0)),
            'Close': format_currency(price.get('close', 0)),
            'Volume': format_volume(price.get('volume', 0)),
            'Change': f"{change:+,.0f}",
            'Change %': f"{change_pct:+.2f}%"
        })
    
    df = pd.DataFrame(table_data)
    
    st.subheader(f"{symbol} Price History")
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Open": st.column_config.TextColumn("Open", width="small"),
            "High": st.column_config.TextColumn("High", width="small"),
            "Low": st.column_config.TextColumn("Low", width="small"),
            "Close": st.column_config.TextColumn("Close", width="small"),
            "Volume": st.column_config.TextColumn("Volume", width="small"),
            "Change": st.column_config.TextColumn("Change", width="small"),
            "Change %": st.column_config.TextColumn("Change %", width="small")
        }
    )

def create_sector_summary_table(stocks: List[Dict[str, Any]]):
    """Create sector summary table"""
    if not stocks:
        st.info("No stocks data available")
        return
    
    # Group by sector
    sector_data = {}
    for stock in stocks:
        sector = stock.get('sector', 'Unknown')
        if sector not in sector_data:
            sector_data[sector] = {
                'count': 0,
                'avg_score': 0,
                'buy_count': 0,
                'hold_count': 0,
                'sell_count': 0,
                'scores': []
            }
        
        sector_data[sector]['count'] += 1
        
        score = stock.get('combined_score', 0)
        if score:
            sector_data[sector]['scores'].append(score)
        
        rec = stock.get('recommendation', '').upper()
        if rec == 'BUY':
            sector_data[sector]['buy_count'] += 1
        elif rec == 'HOLD':
            sector_data[sector]['hold_count'] += 1
        elif rec == 'SELL':
            sector_data[sector]['sell_count'] += 1
    
    # Prepare table data
    table_data = []
    for sector, data in sector_data.items():
        avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
        
        table_data.append({
            'Sector': sector,
            'Stocks': data['count'],
            'Avg Score': format_score(avg_score),
            'BUY': data['buy_count'],
            'HOLD': data['hold_count'],
            'SELL': data['sell_count']
        })
    
    df = pd.DataFrame(table_data)
    df = df.sort_values('Avg Score', ascending=False, key=lambda x: pd.to_numeric(x, errors='coerce'))
    
    st.subheader("Sector Summary")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sector": st.column_config.TextColumn("Sector", width="medium"),
            "Stocks": st.column_config.NumberColumn("Stocks", width="small"),
            "Avg Score": st.column_config.TextColumn("Avg Score", width="small"),
            "BUY": st.column_config.NumberColumn("BUY", width="small"),
            "HOLD": st.column_config.NumberColumn("HOLD", width="small"),
            "SELL": st.column_config.NumberColumn("SELL", width="small")
        }
    )