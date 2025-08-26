"""
Metric display components for AlphaGen Dashboard

Reusable metric display widgets and cards.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from ..utils.formatting import (
    format_currency, format_percentage, format_score, format_sentiment,
    format_recommendation, get_recommendation_color, get_sentiment_color,
    get_confidence_color, get_score_emoji
)

def display_stock_card(stock_data: Dict[str, Any], large: bool = False):
    """Display stock information card"""
    if not stock_data:
        st.error("No stock data available")
        return
    
    symbol = stock_data.get('symbol', 'N/A')
    company_name = stock_data.get('company_name', 'N/A')
    recommendation = stock_data.get('recommendation')
    score = stock_data.get('composite_score')
    
    # Determine card size
    if large:
        st.markdown(f"""
        <div style="
            border: 2px solid {get_recommendation_color(recommendation)};
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        ">
            <h1 style="margin: 0; color: {get_recommendation_color(recommendation)};">
                {format_recommendation(recommendation)}
            </h1>
            <h2 style="margin: 5px 0; color: #333;">{symbol}</h2>
            <h3 style="margin: 5px 0; color: #666;">{company_name}</h3>
            <h2 style="margin: 10px 0; color: {get_recommendation_color(recommendation)};">
                Score: {format_score(score)} {get_score_emoji(score)}
            </h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.metric("Symbol", symbol)
        with col2:
            st.metric("Company", company_name[:20] + "..." if len(company_name) > 20 else company_name)
        with col3:
            st.metric("Score", format_score(score), delta=format_recommendation(recommendation))

def show_score_breakdown(scores: Dict[str, float], title: str = "Score Breakdown"):
    """Display score components with visual indicators"""
    st.subheader(title)
    
    if not scores:
        st.info("No score data available")
        return
    
    cols = st.columns(len(scores))
    
    for i, (metric, score) in enumerate(scores.items()):
        with cols[i]:
            color = get_recommendation_color("BUY" if score and score > 70 else "HOLD" if score and score > 40 else "SELL")
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border: 1px solid {color}; border-radius: 5px;">
                <h4 style="margin: 0; color: {color};">{metric.replace('_', ' ').title()}</h4>
                <h2 style="margin: 5px 0; color: {color};">{format_score(score)} {get_score_emoji(score)}</h2>
            </div>
            """, unsafe_allow_html=True)

def display_recommendation_badge(recommendation: str, confidence: str = None):
    """Display recommendation as a styled badge"""
    color = get_recommendation_color(recommendation)
    conf_color = get_confidence_color(confidence) if confidence else color
    
    badge_html = f"""
    <div style="
        display: inline-block;
        background-color: {color};
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
        text-align: center;
    ">
        {format_recommendation(recommendation)}
        {f'<br><small>({confidence} confidence)</small>' if confidence else ''}
    </div>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)

def display_metric_cards(metrics: List[Dict[str, Any]]):
    """Display multiple metrics as cards in columns"""
    if not metrics:
        st.info("No metrics available")
        return
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            title = metric.get('title', 'Metric')
            value = metric.get('value', 'N/A')
            delta = metric.get('delta')
            help_text = metric.get('help')
            
            st.metric(
                label=title,
                value=value,
                delta=delta,
                help=help_text
            )

def display_sentiment_indicator(sentiment: float, title: str = "Sentiment"):
    """Display sentiment with color-coded indicator"""
    color = get_sentiment_color(sentiment)
    sentiment_text = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
    
    st.markdown(f"""
    <div style="
        padding: 10px;
        border-left: 5px solid {color};
        background-color: rgba(128, 128, 128, 0.1);
        margin: 10px 0;
    ">
        <h4 style="margin: 0; color: {color};">{title}</h4>
        <p style="margin: 5px 0; color: {color}; font-weight: bold;">
            {sentiment_text} ({format_sentiment(sentiment)})
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_key_themes(themes: List[str], title: str = "Key Themes"):
    """Display themes as styled tags"""
    if not themes:
        return
    
    st.subheader(title)
    
    # Create HTML for theme tags
    tags_html = ""
    for theme in themes[:10]:  # Limit to 10 themes
        tags_html += f"""
        <span style="
            display: inline-block;
            background-color: #e1f5fe;
            color: #01579b;
            padding: 4px 8px;
            margin: 2px;
            border-radius: 12px;
            font-size: 12px;
            border: 1px solid #b3e5fc;
        ">{theme}</span>
        """
    
    st.markdown(f'<div style="margin: 10px 0;">{tags_html}</div>', unsafe_allow_html=True)

def display_health_status(health_data: Dict[str, Any]):
    """Display system health status"""
    if not health_data:
        st.error("Unable to fetch health status")
        return
    
    status = health_data.get('status', 'unknown')
    
    if status == 'healthy':
        st.success("🟢 System Status: Healthy")
    elif status == 'degraded':
        st.warning("🟡 System Status: Degraded")
    else:
        st.error("🔴 System Status: Unhealthy")
    
    # Show additional details in expander
    with st.expander("System Details"):
        for key, value in health_data.items():
            if key != 'status':
                st.text(f"{key.replace('_', ' ').title()}: {value}")

def display_market_overview(market_data: Dict[str, Any]):
    """Display market overview metrics"""
    if not market_data:
        st.info("No market data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sentiment = market_data.get('overall_sentiment', 0)
        st.metric(
            "Market Sentiment", 
            format_sentiment(sentiment),
            delta=market_data.get('sentiment_label', 'Neutral')
        )
    
    with col2:
        st.metric(
            "Total Articles",
            market_data.get('total_articles', 0)
        )
    
    with col3:
        st.metric(
            "Trend Direction",
            market_data.get('trending_direction', 'stable').title()
        )
    
    with col4:
        st.metric(
            "Analysis Date",
            market_data.get('analysis_date', 'N/A')
        )

def display_performance_metrics(data: Dict[str, Any]):
    """Display performance metrics for a stock"""
    if not data:
        return
    
    metrics = []
    
    latest_analysis = data.get('latest_analysis', {})
    quant_metrics = latest_analysis.get('quantitative_metrics', {})
    qual_metrics = latest_analysis.get('qualitative_metrics', {})
    
    # Add quantitative metrics
    if quant_metrics.get('pe_ratio'):
        metrics.append({
            'title': 'P/E Ratio',
            'value': f"{quant_metrics['pe_ratio']:.2f}",
            'help': 'Price to Earnings ratio'
        })
    
    if quant_metrics.get('pb_ratio'):
        metrics.append({
            'title': 'P/B Ratio', 
            'value': f"{quant_metrics['pb_ratio']:.2f}",
            'help': 'Price to Book ratio'
        })
    
    if quant_metrics.get('rsi'):
        metrics.append({
            'title': 'RSI',
            'value': f"{quant_metrics['rsi']:.1f}",
            'help': 'Relative Strength Index'
        })
    
    # Add qualitative metrics
    if qual_metrics.get('sentiment_score') is not None:
        metrics.append({
            'title': 'Sentiment',
            'value': format_sentiment(qual_metrics['sentiment_score']),
            'help': 'News sentiment score'
        })
    
    if metrics:
        display_metric_cards(metrics)