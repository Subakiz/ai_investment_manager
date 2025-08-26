"""
Trending Themes Page for AlphaGen Dashboard

Analysis of trending financial themes and narratives.
"""

import streamlit as st
from ..utils.api_client import get_api_client
from ..components.charts import create_theme_frequency_chart
from ..components.tables import create_themes_table
from ..utils.formatting import format_sentiment, format_date

def show():
    """Display the trending themes page"""
    
    st.title("🏷️ Trending Financial Themes")
    st.markdown("*AI-powered analysis of emerging themes and narratives in Indonesian markets*")
    
    api_client = get_api_client()
    
    # Controls for theme analysis
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Time period selector
        days = st.selectbox(
            "Analysis period:",
            [1, 2, 3, 7, 14, 30],
            index=1,  # Default to 2 days
            help="Number of days to analyze for trending themes",
            key="theme_days_selector"
        )
    
    with col2:
        if st.button("🔄 Refresh Themes", key="refresh_themes"):
            api_client.clear_cache()
            st.rerun()
    
    with col3:
        st.metric("Analysis Period", f"{days} days")
    
    # Get themes data
    themes_data = api_client.get_top_themes(days=days)
    
    if not themes_data:
        st.error("Cannot load themes data. Please check API connection.")
        return
    
    themes = themes_data.get('top_themes', [])
    analysis_period = themes_data.get('analysis_period', 'Unknown period')
    
    if not themes:
        st.warning(f"No trending themes found for the last {days} days. Try expanding the analysis period.")
        return
    
    # Overview metrics
    st.markdown("---")
    col4, col5, col6, col7 = st.columns(4)
    
    with col4:
        st.metric("Total Themes", len(themes))
    
    with col5:
        total_mentions = sum(theme.get('occurrence_count', 0) for theme in themes)
        st.metric("Total Mentions", total_mentions)
    
    with col6:
        avg_sentiment = sum(theme.get('avg_sentiment', 0) for theme in themes) / len(themes)
        sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
        st.metric("Avg Sentiment", sentiment_label, delta=format_sentiment(avg_sentiment))
    
    with col7:
        unique_stocks = set()
        for theme in themes:
            unique_stocks.update(theme.get('related_stocks', []))
        st.metric("Stocks Affected", len(unique_stocks))
    
    # Main themes visualization
    st.markdown("---")
    st.subheader("📊 Theme Frequency Analysis")
    
    col8, col9 = st.columns([3, 1])
    
    with col8:
        # Theme frequency chart
        fig = create_theme_frequency_chart(themes[:15])  # Top 15 themes
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col9:
        st.markdown("**🎯 Top 5 Themes:**")
        
        for i, theme in enumerate(themes[:5], 1):
            theme_name = theme.get('theme', '')
            mentions = theme.get('occurrence_count', 0)
            sentiment = theme.get('avg_sentiment', 0)
            
            # Sentiment emoji
            if sentiment > 0.2:
                emoji = "🚀"
            elif sentiment > 0.1:
                emoji = "😊"
            elif sentiment > -0.1:
                emoji = "😐"
            elif sentiment > -0.2:
                emoji = "😟"
            else:
                emoji = "📉"
            
            st.markdown(f"""
            **{i}. {theme_name}** {emoji}
            - 📈 {mentions} mentions
            - 😊 {format_sentiment(sentiment)}
            """)
    
    # Detailed themes table
    st.markdown("---")
    st.subheader("📋 Detailed Themes Analysis")
    
    create_themes_table(themes)
    
    # Theme details and insights
    st.markdown("---")
    st.subheader("🔍 Theme Deep Dive")
    
    # Theme selector for detailed analysis
    theme_options = {theme.get('theme', f'Theme {i}'): i for i, theme in enumerate(themes)}
    
    if theme_options:
        selected_theme_name = st.selectbox(
            "Select a theme for detailed analysis:",
            list(theme_options.keys()),
            key="detailed_theme_selector"
        )
        
        selected_theme_idx = theme_options[selected_theme_name]
        selected_theme = themes[selected_theme_idx]
        
        # Display detailed theme information
        col10, col11 = st.columns([2, 1])
        
        with col10:
            st.markdown(f"### 📌 {selected_theme.get('theme', 'Selected Theme')}")
            
            # Theme metrics
            mentions = selected_theme.get('occurrence_count', 0)
            sentiment = selected_theme.get('avg_sentiment', 0)
            related_stocks = selected_theme.get('related_stocks', [])
            
            # Create metrics display
            col12, col13, col14 = st.columns(3)
            
            with col12:
                st.metric("Mentions", mentions)
            
            with col13:
                st.metric("Avg Sentiment", format_sentiment(sentiment))
            
            with col14:
                st.metric("Related Stocks", len(related_stocks))
            
            # Related stocks display
            if related_stocks:
                st.markdown("**🏢 Related Stocks:**")
                
                # Create clickable stock tags
                stocks_html = ""
                for stock in related_stocks[:10]:  # Limit to 10 stocks
                    stocks_html += f"""
                    <span style="
                        display: inline-block;
                        background-color: #e3f2fd;
                        color: #1976d2;
                        padding: 4px 8px;
                        margin: 2px;
                        border-radius: 12px;
                        font-size: 14px;
                        font-weight: bold;
                        border: 1px solid #bbdefb;
                    ">{stock}</span>
                    """
                
                st.markdown(f'<div style="margin: 10px 0;">{stocks_html}</div>', unsafe_allow_html=True)
        
        with col11:
            # Theme sentiment visualization
            st.markdown("**📊 Sentiment Analysis:**")
            
            # Create a simple sentiment indicator
            sentiment_color = "#4caf50" if sentiment > 0.1 else "#f44336" if sentiment < -0.1 else "#ff9800"
            sentiment_width = int(abs(sentiment) * 100)  # Convert to percentage
            
            st.markdown(f"""
            <div style="margin: 20px 0;">
                <div style="background-color: #f0f0f0; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="
                        background-color: {sentiment_color}; 
                        height: 100%; 
                        width: {sentiment_width}%; 
                        border-radius: 10px;
                        transition: width 0.3s ease;
                    "></div>
                </div>
                <p style="text-align: center; margin: 5px 0; font-size: 14px;">
                    Sentiment Strength: {sentiment_width}%
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sentiment interpretation
            if sentiment > 0.3:
                st.success("🚀 Very Positive Theme")
            elif sentiment > 0.1:
                st.success("😊 Positive Theme")
            elif sentiment > -0.1:
                st.info("😐 Neutral Theme")
            elif sentiment > -0.3:
                st.warning("😟 Negative Theme")
            else:
                st.error("📉 Very Negative Theme")
    
    # Theme categories and insights
    st.markdown("---")
    st.subheader("📈 Theme Categories & Insights")
    
    # Categorize themes by sentiment
    positive_themes = [t for t in themes if t.get('avg_sentiment', 0) > 0.1]
    neutral_themes = [t for t in themes if -0.1 <= t.get('avg_sentiment', 0) <= 0.1]
    negative_themes = [t for t in themes if t.get('avg_sentiment', 0) < -0.1]
    
    col15, col16, col17 = st.columns(3)
    
    with col15:
        st.markdown("### 🟢 Positive Themes")
        if positive_themes:
            for theme in positive_themes[:5]:
                theme_name = theme.get('theme', '')
                mentions = theme.get('occurrence_count', 0)
                st.markdown(f"• **{theme_name}** ({mentions} mentions)")
        else:
            st.info("No strongly positive themes found")
    
    with col16:
        st.markdown("### 🟡 Neutral Themes")
        if neutral_themes:
            for theme in neutral_themes[:5]:
                theme_name = theme.get('theme', '')
                mentions = theme.get('occurrence_count', 0)
                st.markdown(f"• **{theme_name}** ({mentions} mentions)")
        else:
            st.info("No neutral themes found")
    
    with col17:
        st.markdown("### 🔴 Negative Themes")
        if negative_themes:
            for theme in negative_themes[:5]:
                theme_name = theme.get('theme', '')
                mentions = theme.get('occurrence_count', 0)
                st.markdown(f"• **{theme_name}** ({mentions} mentions)")
        else:
            st.info("No strongly negative themes found")
    
    # Analysis summary
    st.markdown("---")
    st.subheader("📋 Analysis Summary")
    
    col18, col19 = st.columns([2, 1])
    
    with col18:
        st.markdown("**🎯 Key Insights:**")
        
        # Generate insights based on data
        insights = []
        
        if len(positive_themes) > len(negative_themes):
            insights.append(f"✅ Market themes are predominantly positive ({len(positive_themes)} vs {len(negative_themes)} negative themes)")
        elif len(negative_themes) > len(positive_themes):
            insights.append(f"⚠️ Market themes show concerning trends ({len(negative_themes)} negative vs {len(positive_themes)} positive themes)")
        else:
            insights.append("⚖️ Market themes are balanced between positive and negative sentiment")
        
        if total_mentions > 100:
            insights.append(f"📈 High theme activity with {total_mentions} total mentions across all themes")
        elif total_mentions > 50:
            insights.append(f"📊 Moderate theme activity with {total_mentions} total mentions")
        else:
            insights.append(f"📉 Low theme activity with only {total_mentions} total mentions")
        
        if len(unique_stocks) > 20:
            insights.append(f"🏢 Broad market impact across {len(unique_stocks)} different stocks")
        else:
            insights.append(f"🎯 Focused impact on {len(unique_stocks)} specific stocks")
        
        for insight in insights:
            st.markdown(f"- {insight}")
    
    with col19:
        st.markdown(f"**📊 Summary Statistics:**")
        st.markdown(f"- Analysis Period: {analysis_period}")
        st.markdown(f"- Total Themes: {len(themes)}")
        st.markdown(f"- Average Sentiment: {format_sentiment(avg_sentiment)}")
        st.markdown(f"- Most Active Theme: {themes[0].get('theme', 'N/A') if themes else 'N/A'}")
        st.markdown(f"- Highest Sentiment: {max(themes, key=lambda x: x.get('avg_sentiment', 0)).get('theme', 'N/A') if themes else 'N/A'}")
    
    # Footer with methodology
    st.markdown("---")
    with st.expander("🔬 Theme Analysis Methodology"):
        st.markdown("""
        **How Themes Are Identified:**
        
        1. **Content Analysis**: AI extracts key themes from financial news articles
        2. **Theme Normalization**: Similar themes are grouped together (e.g., "digital banking", "digital transformation")
        3. **Occurrence Counting**: Themes are counted across all articles in the time period
        4. **Sentiment Aggregation**: Average sentiment is calculated for each theme
        5. **Stock Association**: Themes are linked to mentioned stocks for impact analysis
        
        **Theme Categories Include:**
        - **Business Strategy**: Digital transformation, expansion plans, partnerships
        - **Financial Performance**: Earnings, revenue growth, profitability
        - **Market Conditions**: Interest rates, economic indicators, policy changes
        - **Industry Trends**: Regulatory changes, technology adoption, competition
        - **Corporate Actions**: Mergers, acquisitions, management changes
        
        **Interpretation Guidelines:**
        - **High occurrence + positive sentiment**: Favorable market trends
        - **High occurrence + negative sentiment**: Market concerns or risks
        - **Low occurrence themes**: Emerging or niche topics
        - **Broad stock impact**: Systemic themes affecting multiple companies
        
        **Data Freshness**: Themes are updated in real-time as new articles are processed.
        """)

if __name__ == "__main__":
    show()