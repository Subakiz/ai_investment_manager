"""
API Client for AlphaGen Dashboard

Handles communication with the FastAPI backend.
"""

import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import json

class AlphaGenAPIClient:
    """Client for communicating with AlphaGen FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"API Error: {e}")
            return None
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON response: {e}")
            return None
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_latest_recommendation(_self) -> Optional[Dict[str, Any]]:
        """Get the top-ranked stock recommendation"""
        return _self._make_request("/recommendations/latest")
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_stock_analysis(_self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis for a specific stock"""
        return _self._make_request(f"/stocks/{symbol}/analysis")
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_market_sentiment(_self) -> Optional[Dict[str, Any]]:
        """Get market sentiment overview"""
        return _self._make_request("/market/sentiment")
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_top_themes(_self, days: int = 2) -> Optional[Dict[str, Any]]:
        """Get trending themes"""
        return _self._make_request(f"/themes/top?days={days}")
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes  
    def get_stocks_list(_self, lq45_only: bool = True) -> Optional[Dict[str, Any]]:
        """Get list of stocks with scores"""
        return _self._make_request(f"/stocks/list?lq45_only={lq45_only}")
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_stock_prices(_self, symbol: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get stock price history"""
        return _self._make_request(f"/stocks/{symbol}/prices?days={days}")
    
    @st.cache_data(ttl=60)   # Cache for 1 minute
    def get_health(_self) -> Optional[Dict[str, Any]]:
        """Get API health status"""
        return _self._make_request("/health")
    
    def clear_cache(self):
        """Clear all cached data"""
        st.cache_data.clear()

# Global API client instance
@st.cache_resource
def get_api_client():
    """Get cached API client instance"""
    return AlphaGenAPIClient()