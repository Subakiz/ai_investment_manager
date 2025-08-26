"""
Stock Detail Page for AlphaGen Dashboard

Detailed analysis for individual stocks.
"""

import streamlit as st
from ..utils.api_client import get_api_client
from ..components.metrics import (
    display_stock_card, display_performance_metrics, display_key_themes
)
from ..components.charts import (
    create_price_chart, create_score_radar
)
from ..components.tables import (
    create_news_table, create_price_history_table
)
from ..utils.formatting import format_score, format_sentiment

def show():
    """Display the stock detail page"""
    
    st.title("🔍 Stock Analysis")
    st.markdown("*Deep dive into individual stock performance and analysis*")
    
    api_client = get_api_client()
    
    # Stock selector
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get stocks list for selector
        stocks_data = api_client.get_stocks_list()
        if stocks_data:
            stocks = stocks_data.get('stocks', [])
            stock_options = {f"{s['symbol']} - {s['company_name']}": s['symbol'] 
                           for s in stocks if s.get('symbol')}
            
            if stock_options:
                selected_option = st.selectbox(
                    "Select a stock to analyze:",
                    list(stock_options.keys()),
                    key="stock_selector"
                )
                selected_symbol = stock_options[selected_option]
            else:
                st.warning("No stocks available for analysis")
                return
        else:
            st.error("Cannot load stocks list. Please check API connection.")
            return
    
    with col2:
        if st.button("🔄 Refresh Analysis", key="refresh_stock_analysis"):
            api_client.clear_cache()
            st.rerun()
    
    if not selected_symbol:
        st.info("Please select a stock to view its analysis.")
        return
    
    # Get detailed analysis for selected stock
    stock_analysis = api_client.get_stock_analysis(selected_symbol)
    
    if not stock_analysis:
        st.error(f"Cannot load analysis for {selected_symbol}. Data may not be available.")
        return
    
    # Display stock header
    col3, col4 = st.columns([2, 1])
    
    with col3:
        st.subheader(f"📊 {stock_analysis.get('symbol')} Analysis")
        st.markdown(f"**{stock_analysis.get('company_name', 'N/A')}**")
        
        # Get basic stock info from stocks list
        stock_info = next((s for s in stocks if s['symbol'] == selected_symbol), {})
        if stock_info:
            display_stock_card(stock_info)
    
    with col4:
        # Quick metrics
        latest_analysis = stock_analysis.get('latest_analysis', {})
        if latest_analysis:
            analysis_date = latest_analysis.get('analysis_date', 'N/A')
            st.metric("Analysis Date", analysis_date)
            
            quant_metrics = latest_analysis.get('quantitative_metrics', {})
            qual_metrics = latest_analysis.get('qualitative_metrics', {})
            
            if quant_metrics.get('composite_score') is not None:
                st.metric("Quantitative Score", format_score(quant_metrics['composite_score']))
            
            if qual_metrics.get('sentiment_score') is not None:
                st.metric("Sentiment Score", format_sentiment(qual_metrics['sentiment_score']))
    
    # Performance metrics section
    st.markdown("---")
    st.subheader("📈 Performance Metrics")
    
    if latest_analysis:
        display_performance_metrics(stock_analysis)
        
        # Create radar chart for scores
        quant_metrics = latest_analysis.get('quantitative_metrics', {})
        if any(quant_metrics.values()):
            radar_data = {}
            
            if quant_metrics.get('composite_score') is not None:
                radar_data['Overall'] = quant_metrics['composite_score']
            
            # Add individual metrics (convert to 0-100 scale)
            if quant_metrics.get('pe_ratio'):
                # Simple scoring for P/E (lower is better, cap at 25)
                pe_score = max(0, 100 - (quant_metrics['pe_ratio'] - 10) * 5)
                radar_data['Valuation'] = min(100, max(0, pe_score))
            
            if quant_metrics.get('rsi'):
                # RSI scoring (optimal around 50)
                rsi = quant_metrics['rsi']
                rsi_score = 100 - abs(rsi - 50)
                radar_data['Technical'] = max(0, rsi_score)
            
            qual_metrics = latest_analysis.get('qualitative_metrics', {})
            if qual_metrics.get('sentiment_score') is not None:
                # Convert sentiment (-1 to 1) to 0-100 scale
                sentiment_score = (qual_metrics['sentiment_score'] + 1) * 50
                radar_data['Sentiment'] = sentiment_score
            
            if len(radar_data) >= 3:
                col5, col6 = st.columns([2, 1])
                
                with col5:
                    fig = create_score_radar(radar_data, f"{selected_symbol} Analysis Scores")
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                with col6:
                    st.markdown("**Score Breakdown:**")
                    for metric, score in radar_data.items():
                        st.metric(metric, f"{score:.1f}/100")
    
    # Price chart and history section
    st.markdown("---")
    st.subheader("💹 Price Analysis")
    
    col7, col8 = st.columns([2, 1])
    
    with col7:
        # Get price history
        price_data = api_client.get_stock_prices(selected_symbol, days=30)
        if price_data and price_data.get('prices'):
            prices = price_data['prices']
            
            # Create price chart
            fig = create_price_chart(prices, selected_symbol)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Price history not available")
    
    with col8:
        # Price statistics
        if price_data and price_data.get('prices'):
            prices = price_data['prices']
            
            if prices:
                latest_price = prices[0]  # Most recent price
                oldest_price = prices[-1]  # Oldest price in dataset
                
                current_price = latest_price.get('close', 0)
                old_price = oldest_price.get('close', 0)
                
                if current_price and old_price:
                    change = current_price - old_price
                    change_pct = (change / old_price) * 100
                    
                    st.metric(
                        "Current Price", 
                        f"Rp {current_price:,.0f}",
                        delta=f"{change:+,.0f} ({change_pct:+.1f}%)"
                    )
                
                # Volume statistics
                volumes = [p.get('volume', 0) for p in prices if p.get('volume')]
                if volumes:
                    avg_volume = sum(volumes) / len(volumes)
                    latest_volume = latest_price.get('volume', 0)
                    
                    st.metric(
                        "Latest Volume",
                        f"{latest_volume:,.0f}",
                        delta=f"Avg: {avg_volume:,.0f}"
                    )
    
    # News analysis section
    st.markdown("---")
    st.subheader("📰 Recent News Analysis")
    
    recent_news = stock_analysis.get('recent_news', [])
    if recent_news:
        create_news_table(recent_news, show_sentiment=True)
        
        # News insights
        if len(recent_news) >= 3:
            col9, col10 = st.columns(2)
            
            with col9:
                # Calculate average sentiment
                sentiments = [n.get('sentiment_score') for n in recent_news 
                            if n.get('sentiment_score') is not None]
                if sentiments:
                    avg_sentiment = sum(sentiments) / len(sentiments)
                    st.metric("Average News Sentiment", format_sentiment(avg_sentiment))
            
            with col10:
                # Show confidence
                confidences = [n.get('confidence') for n in recent_news 
                             if n.get('confidence') is not None]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    st.metric("Average Confidence", f"{avg_confidence:.2f}")
    else:
        st.info("No recent news available for this stock")
    
    # Key themes section
    if latest_analysis:
        qual_metrics = latest_analysis.get('qualitative_metrics', {})
        themes = qual_metrics.get('themes', [])
        if themes:
            st.markdown("---")
            display_key_themes(themes, f"🏷️ Key Themes for {selected_symbol}")
    
    # Historical data table
    if price_data and price_data.get('prices'):
        st.markdown("---")
        with st.expander("📊 Detailed Price History"):
            create_price_history_table(price_data['prices'], selected_symbol)
    
    # Footer with additional info
    st.markdown("---")
    st.markdown(f"""
    **Analysis Summary for {selected_symbol}:**
    - Company: {stock_analysis.get('company_name', 'N/A')}
    - Recent news articles: {len(recent_news)}
    - Price data points: {len(price_data.get('prices', [])) if price_data else 0}
    - Last updated: {latest_analysis.get('analysis_date', 'N/A') if latest_analysis else 'N/A'}
    """)

if __name__ == "__main__":
    show()