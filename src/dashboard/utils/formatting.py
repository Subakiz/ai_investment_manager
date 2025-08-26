"""
Formatting utilities for AlphaGen Dashboard

Handles data formatting, currency, dates, and other display utilities.
"""

import streamlit as st
from datetime import datetime, date
from typing import Union, Optional

def format_currency(amount: Optional[float], currency: str = "IDR") -> str:
    """Format currency amounts for Indonesian market"""
    if amount is None:
        return "-"
    
    if currency == "IDR":
        if amount >= 1_000_000_000:
            return f"Rp {amount/1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"Rp {amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"Rp {amount/1_000:.1f}K"
        else:
            return f"Rp {amount:,.0f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format percentage values"""
    if value is None:
        return "-"
    return f"{value:.{decimals}f}%"

def format_score(score: Optional[float]) -> str:
    """Format analysis scores (0-100)"""
    if score is None:
        return "-"
    return f"{score:.1f}"

def format_sentiment(sentiment: Optional[float]) -> str:
    """Format sentiment scores (-1 to 1)"""
    if sentiment is None:
        return "-"
    return f"{sentiment:+.3f}"

def format_date(date_input: Union[str, datetime, date]) -> str:
    """Format dates for display"""
    if date_input is None:
        return "-"
    
    if isinstance(date_input, str):
        try:
            date_obj = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
        except:
            return date_input
    elif isinstance(date_input, datetime):
        date_obj = date_input
    elif isinstance(date_input, date):
        date_obj = datetime.combine(date_input, datetime.min.time())
    else:
        return str(date_input)
    
    return date_obj.strftime("%d %b %Y")

def format_recommendation(recommendation: Optional[str]) -> str:
    """Format recommendation with emoji"""
    if not recommendation:
        return "-"
    
    rec_map = {
        "BUY": "🚀 BUY",
        "HOLD": "⏸️ HOLD", 
        "SELL": "📉 SELL"
    }
    return rec_map.get(recommendation.upper(), recommendation)

def get_recommendation_color(recommendation: Optional[str]) -> str:
    """Get color for recommendation"""
    if not recommendation:
        return "gray"
    
    color_map = {
        "BUY": "#00C851",    # Green
        "HOLD": "#FF8800",   # Orange
        "SELL": "#FF4444"    # Red
    }
    return color_map.get(recommendation.upper(), "gray")

def get_sentiment_color(sentiment: Optional[float]) -> str:
    """Get color for sentiment score"""
    if sentiment is None:
        return "gray"
    
    if sentiment > 0.1:
        return "#00C851"  # Green
    elif sentiment > -0.1:
        return "#FF8800"  # Orange
    else:
        return "#FF4444"  # Red

def get_confidence_color(confidence: Optional[str]) -> str:
    """Get color for confidence level"""
    if not confidence:
        return "gray"
        
    color_map = {
        "HIGH": "#00C851",    # Green
        "MEDIUM": "#FF8800",  # Orange
        "LOW": "#FF4444"      # Red
    }
    return color_map.get(confidence.upper(), "gray")

def format_volume(volume: Optional[int]) -> str:
    """Format trading volume"""
    if volume is None:
        return "-"
    
    if volume >= 1_000_000_000:
        return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    else:
        return f"{volume:,}"

def format_market_cap(market_cap: Optional[float]) -> str:
    """Format market capitalization"""
    return format_currency(market_cap)

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."

def get_score_emoji(score: Optional[float]) -> str:
    """Get emoji based on score (0-100)"""
    if score is None:
        return "❓"
    
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"