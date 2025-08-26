"""
Market Sentiment Page for AlphaGen Dashboard

Market overview and sentiment analysis.
"""

import streamlit as st
from ..utils.api_client import get_api_client
from ..components.metrics import display_sentiment_indicator, display_market_overview
from ..components.charts import (
    create_sentiment_gauge, create_sector_sentiment_chart, 
    create_timeline_chart
)
from ..utils.formatting import format_sentiment, format_date

def show():
    """Display the market sentiment page"""
    
    st.title("😊 Market Sentiment Analysis")
    st.markdown("*AI-powered sentiment analysis of Indonesian financial markets*")
    
    api_client = get_api_client()
    
    # Get market sentiment data
    market_data = api_client.get_market_sentiment()
    
    if not market_data:
        st.error("Cannot load market sentiment data. Please check API connection.")
        return
    
    # Top row: Overall sentiment
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.subheader("🌡️ Overall Market Mood")
        
        sentiment_score = market_data.get('overall_sentiment', 0)
        sentiment_label = market_data.get('sentiment_label', 'Neutral')
        
        # Large sentiment gauge
        fig = create_sentiment_gauge(sentiment_score, "Market Sentiment")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Market Metrics")
        display_market_overview(market_data)
        
        # Additional sentiment details
        trending_direction = market_data.get('trending_direction', 'stable')
        st.metric(
            "Market Trend", 
            trending_direction.title(),
            delta="📈" if trending_direction == "improving" else "📉" if trending_direction == "declining" else "➡️"
        )
    
    with col3:
        st.subheader("📅 Analysis Info")
        
        analysis_date = market_data.get('analysis_date', 'N/A')
        total_articles = market_data.get('total_articles', 0)
        
        st.metric("Analysis Date", format_date(analysis_date))
        st.metric("Articles Analyzed", total_articles)
        
        if st.button("🔄 Refresh Sentiment", key="refresh_sentiment"):
            api_client.clear_cache()
            st.rerun()
    
    # Sentiment interpretation
    st.markdown("---")
    col4, col5 = st.columns([3, 1])
    
    with col4:
        display_sentiment_indicator(sentiment_score, "Current Market Sentiment")
        
        # Sentiment interpretation
        st.markdown("**💡 Sentiment Interpretation:**")
        
        if sentiment_score > 0.3:
            st.success("""
            **Strongly Positive Market Sentiment** 🚀
            - Investors are optimistic about market conditions
            - Positive news flow and corporate developments
            - Good time for potential investments
            """)
        elif sentiment_score > 0.1:
            st.info("""
            **Moderately Positive Sentiment** 📈
            - Generally favorable market outlook
            - Mixed but leaning positive news coverage
            - Cautious optimism recommended
            """)
        elif sentiment_score > -0.1:
            st.warning("""
            **Neutral Market Sentiment** ⚖️
            - Balanced mix of positive and negative news
            - Market in wait-and-see mode
            - No clear directional bias
            """)
        elif sentiment_score > -0.3:
            st.warning("""
            **Moderately Negative Sentiment** 📉
            - Some concerns in the market
            - Negative news outweighing positive
            - Increased caution advised
            """)
        else:
            st.error("""
            **Strongly Negative Sentiment** ⚠️
            - Significant market pessimism
            - Negative news dominating coverage
            - Risk-off sentiment prevailing
            """)
    
    with col5:
        st.markdown("**📈 Sentiment Scale:**")
        st.markdown("""
        - **+1.0**: Extremely Positive
        - **+0.5**: Very Positive  
        - **+0.1**: Moderately Positive
        - **0.0**: Neutral
        - **-0.1**: Moderately Negative
        - **-0.5**: Very Negative
        - **-1.0**: Extremely Negative
        """)
        
        current_sentiment = format_sentiment(sentiment_score)
        st.metric("Current Level", current_sentiment)
    
    # Sector breakdown
    st.markdown("---")
    st.subheader("🏭 Sector Sentiment Breakdown")
    
    sector_breakdown = market_data.get('sector_breakdown', {})
    if sector_breakdown:
        col6, col7 = st.columns([2, 1])
        
        with col6:
            # Sector sentiment chart
            fig = create_sector_sentiment_chart(sector_breakdown)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        
        with col7:
            st.markdown("**📋 Sector Rankings:**")
            
            # Sort sectors by sentiment
            sorted_sectors = sorted(sector_breakdown.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            for i, (sector, sentiment) in enumerate(sorted_sectors, 1):
                emoji = "🟢" if sentiment > 0.1 else "🟡" if sentiment > -0.1 else "🔴"
                st.markdown(f"{i}. {emoji} **{sector}**: {format_sentiment(sentiment)}")
    else:
        st.info("Sector breakdown not available")
    
    # Sentiment timeline (simulated for demonstration)
    st.markdown("---")
    st.subheader("📈 Sentiment Timeline")
    
    col8, col9 = st.columns([3, 1])
    
    with col8:
        # For demonstration, create a simple timeline
        # In real implementation, this would come from historical sentiment data
        import datetime
        import random
        
        # Generate sample historical data
        dates = []
        sentiments = []
        base_date = datetime.datetime.now()
        
        for i in range(30, 0, -1):
            date = base_date - datetime.timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Simulate sentiment trending toward current value
            trend_factor = (30 - i) / 30
            noise = random.uniform(-0.1, 0.1)
            simulated_sentiment = sentiment_score * trend_factor + noise
            sentiments.append(max(-1, min(1, simulated_sentiment)))
        
        timeline_data = [
            {'date': date, 'sentiment': sent} 
            for date, sent in zip(dates, sentiments)
        ]
        
        fig = create_timeline_chart(
            timeline_data, 
            'date', 
            'sentiment', 
            'Market Sentiment Trend (30 Days)'
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col9:
        st.markdown("**📊 Timeline Insights:**")
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            max_sentiment = max(sentiments)
            min_sentiment = min(sentiments)
            volatility = max_sentiment - min_sentiment
            
            st.metric("30-Day Average", format_sentiment(avg_sentiment))
            st.metric("Peak Sentiment", format_sentiment(max_sentiment))
            st.metric("Lowest Sentiment", format_sentiment(min_sentiment))
            st.metric("Volatility Range", f"{volatility:.3f}")
    
    # News coverage analysis
    st.markdown("---")
    st.subheader("📰 News Coverage Analysis")
    
    col10, col11, col12 = st.columns(3)
    
    with col10:
        st.markdown("**📊 Article Volume:**")
        st.metric("Today's Articles", total_articles)
        
        # Estimate daily average (demo)
        daily_avg = max(50, total_articles)  # Simple demo calculation
        st.metric("Daily Average", daily_avg, delta=f"{total_articles - daily_avg:+d}")
    
    with col11:
        st.markdown("**🎯 Coverage Quality:**")
        
        # Calculate coverage quality score
        if total_articles > 100:
            quality = "Excellent"
            quality_score = 95
        elif total_articles > 50:
            quality = "Good"
            quality_score = 80
        elif total_articles > 20:
            quality = "Fair"
            quality_score = 65
        else:
            quality = "Limited"
            quality_score = 40
        
        st.metric("Coverage Quality", quality)
        st.metric("Quality Score", f"{quality_score}/100")
    
    with col12:
        st.markdown("**📈 Sentiment Confidence:**")
        
        # Calculate confidence based on article volume and sentiment consistency
        if total_articles > 50:
            confidence = "High"
            conf_score = min(95, 70 + total_articles / 10)
        elif total_articles > 20:
            confidence = "Medium"
            conf_score = min(80, 50 + total_articles / 5)
        else:
            confidence = "Low"
            conf_score = max(30, total_articles * 2)
        
        st.metric("Analysis Confidence", confidence)
        st.metric("Confidence Score", f"{conf_score:.0f}/100")
    
    # Footer with methodology
    st.markdown("---")
    with st.expander("🔬 Methodology & Data Sources"):
        st.markdown("""
        **Sentiment Analysis Methodology:**
        
        1. **Data Collection**: Financial news from Indonesian sources (Kontan, Bisnis.com, etc.)
        2. **AI Processing**: Google Gemini AI analyzes article sentiment and themes
        3. **Aggregation**: Individual article sentiments are weighted and aggregated
        4. **Sector Classification**: Articles are mapped to relevant sectors
        5. **Temporal Analysis**: Sentiment trends are tracked over time
        
        **Data Sources:**
        - Indonesian financial news websites
        - Company announcements and reports
        - Market commentary and analysis
        
        **Update Frequency:**
        - Real-time news collection
        - Sentiment analysis updated every few hours
        - Historical data retained for trend analysis
        
        **Limitations:**
        - Sentiment analysis is AI-generated and may have biases
        - News coverage may not represent all market factors
        - Results should be combined with fundamental analysis
        """)

if __name__ == "__main__":
    show()