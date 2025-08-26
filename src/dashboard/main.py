"""
AlphaGen Investment Platform Dashboard

Main Streamlit application for visualizing investment insights.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Configure Streamlit page
st.set_page_config(
    page_title="AlphaGen Investment Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import dashboard modules
from pages import overview, stock_detail, market_sentiment, themes
from utils.api_client import get_api_client
from components.metrics import display_health_status

def main():
    """Main dashboard application"""
    
    # Sidebar navigation
    st.sidebar.title("🚀 AlphaGen")
    st.sidebar.markdown("*Indonesian Stock Market AI Platform*")
    
    # Check API health
    api_client = get_api_client()
    health_data = api_client.get_health()
    
    if health_data:
        status = health_data.get('status', 'unknown')
        if status == 'healthy':
            st.sidebar.success("🟢 API Connected")
        else:
            st.sidebar.warning("🟡 API Issues")
    else:
        st.sidebar.error("🔴 API Offline")
        st.error("""
        **API Connection Failed**
        
        Please ensure the FastAPI backend is running:
        ```bash
        cd /path/to/ai_investment_manager
        python -m src.api.main
        ```
        
        The API should be available at: http://localhost:8000
        """)
        return
    
    # Navigation menu
    pages = {
        "📊 Market Overview": overview,
        "🔍 Stock Analysis": stock_detail,
        "😊 Market Sentiment": market_sentiment,
        "🏷️ Trending Themes": themes
    }
    
    selected_page = st.sidebar.selectbox(
        "Navigate to:",
        list(pages.keys()),
        key="page_selector"
    )
    
    # Add refresh button
    if st.sidebar.button("🔄 Refresh Data", key="global_refresh"):
        api_client.clear_cache()
        st.rerun()
    
    # Display health status in sidebar
    with st.sidebar.expander("System Status"):
        display_health_status(health_data)
    
    # Add sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("**About AlphaGen**")
    st.sidebar.info("""
    AI-powered investment platform for Indonesian Stock Exchange (IDX).
    
    **Features:**
    - Real-time market analysis
    - AI sentiment analysis
    - LQ45 stock recommendations
    - Technical & fundamental analysis
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Phase 3: Dashboard & API*")
    st.sidebar.markdown("*Version 1.0.0*")
    
    # Main content area
    try:
        # Run selected page
        pages[selected_page].show()
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()