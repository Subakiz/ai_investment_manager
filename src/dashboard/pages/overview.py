"""
Market Overview Page for AlphaGen Dashboard

Main dashboard page showing top recommendation and market snapshot.
"""

import streamlit as st
from ..utils.api_client import get_api_client
from ..components.metrics import (
    display_stock_card, display_market_overview, display_key_themes
)
from ..components.charts import (
    create_sentiment_gauge, create_recommendation_distribution
)
from ..components.tables import create_stocks_ranking, create_sector_summary_table

def show():
    """Display the market overview page"""
    
    st.title("📊 Market Overview")
    st.markdown("*Your AI-powered Indonesian stock market dashboard*")
    
    api_client = get_api_client()
    
    # Top row: Main recommendation and market sentiment
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Top Recommendation")
        
        # Get latest recommendation
        latest_rec = api_client.get_latest_recommendation()
        if latest_rec:
            display_stock_card(latest_rec, large=True)
            
            # Show key themes
            themes = latest_rec.get('key_themes', [])
            if themes:
                display_key_themes(themes, "📌 Key Investment Themes")
        else:
            st.warning("No recommendations available. Check if the analysis engine is running.")
    
    with col2:
        st.subheader("🌡️ Market Mood")
        
        # Get market sentiment
        market_data = api_client.get_market_sentiment()
        if market_data:
            sentiment_score = market_data.get('overall_sentiment', 0)
            
            # Create sentiment gauge
            fig = create_sentiment_gauge(sentiment_score, "Market Sentiment")
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Display market overview metrics
            display_market_overview(market_data)
        else:
            st.warning("Market sentiment data not available")
    
    # Middle row: Market statistics
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📈 Top Performing Stocks")
        
        # Get stocks list
        stocks_data = api_client.get_stocks_list()
        if stocks_data:
            stocks = stocks_data.get('stocks', [])
            
            # Show top 10 stocks
            top_stocks = [s for s in stocks if s.get('combined_score')][:10]
            if top_stocks:
                create_stocks_ranking(top_stocks, show_scores=True)
            else:
                st.info("No scored stocks available")
        else:
            st.warning("Stocks data not available")
    
    with col4:
        st.subheader("🎯 Recommendation Distribution")
        
        if stocks_data:
            stocks = stocks_data.get('stocks', [])
            recommendations = [s.get('recommendation') for s in stocks if s.get('recommendation')]
            
            if recommendations:
                # Create recommendation pie chart
                fig = create_recommendation_distribution(recommendations)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show sector summary
                create_sector_summary_table(stocks)
            else:
                st.info("No recommendations available")
    
    # Bottom row: Trending themes
    st.markdown("---")
    st.subheader("🏷️ Trending Financial Themes")
    
    col5, col6 = st.columns([3, 1])
    
    with col5:
        # Get trending themes
        themes_data = api_client.get_top_themes(days=3)
        if themes_data:
            themes = themes_data.get('top_themes', [])
            if themes:
                from ..components.charts import create_theme_frequency_chart
                fig = create_theme_frequency_chart(themes[:10])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trending themes found")
        else:
            st.warning("Themes data not available")
    
    with col6:
        # Theme insights
        if themes_data and themes_data.get('top_themes'):
            st.markdown("**📊 Theme Insights**")
            
            analysis_period = themes_data.get('analysis_period', 'Recent days')
            st.info(f"Analysis period: {analysis_period}")
            
            # Show top 5 themes as text
            top_themes = themes_data.get('top_themes', [])[:5]
            for i, theme in enumerate(top_themes, 1):
                theme_name = theme.get('theme', '')
                count = theme.get('occurrence_count', 0)
                sentiment = theme.get('avg_sentiment', 0)
                
                sentiment_emoji = "😊" if sentiment > 0.1 else "😐" if sentiment > -0.1 else "😔"
                
                st.markdown(f"""
                **{i}. {theme_name}** {sentiment_emoji}
                - Mentions: {count}
                - Avg Sentiment: {sentiment:+.2f}
                """)
    
    # Footer with last update time
    st.markdown("---")
    col7, col8, col9 = st.columns([1, 2, 1])
    
    with col8:
        # Show last update info
        if latest_rec:
            analysis_date = latest_rec.get('analysis_date')
            st.info(f"📅 Last Analysis: {analysis_date}")
        
        if market_data:
            article_count = market_data.get('total_articles', 0)
            st.info(f"📰 Articles Analyzed: {article_count}")
    
    # Add refresh instructions
    st.markdown("---")
    st.markdown("💡 **Tip:** Use the refresh button in the sidebar to get the latest data, or navigate to other pages for detailed analysis.")

if __name__ == "__main__":
    show()