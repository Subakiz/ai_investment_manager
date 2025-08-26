"""
Chart components for AlphaGen Dashboard

Reusable chart functions using Plotly and Altair.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional
import numpy as np
from ..utils.formatting import format_currency, get_sentiment_color, get_recommendation_color

def create_price_chart(price_data: List[Dict[str, Any]], symbol: str) -> go.Figure:
    """Create interactive price and volume chart"""
    if not price_data:
        return None
    
    df = pd.DataFrame(price_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Create subplots with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=[f'{symbol} Price', 'Volume'],
        row_heights=[0.7, 0.3]
    )
    
    # Add price line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['close'],
            mode='lines',
            name='Close Price',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{x}<br>Price: Rp %{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add volume bars
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color='rgba(31, 119, 180, 0.6)',
            hovertemplate='%{x}<br>Volume: %{y:,.0f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} Price and Volume Trend",
        height=500,
        showlegend=False,
        xaxis2_title="Date",
        yaxis_title="Price (IDR)",
        yaxis2_title="Volume",
        template="plotly_white"
    )
    
    return fig

def create_sentiment_gauge(sentiment_score: float, title: str = "Market Sentiment") -> go.Figure:
    """Create sentiment gauge chart"""
    # Convert sentiment (-1 to 1) to gauge scale (0 to 100)
    gauge_value = (sentiment_score + 1) * 50
    
    # Determine color based on sentiment
    if sentiment_score > 0.3:
        color = "green"
    elif sentiment_score > -0.3:
        color = "orange" 
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = gauge_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 30], 'color': "lightgray"},
                {'range': [30, 70], 'color': "gray"},
                {'range': [70, 100], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        template="plotly_white"
    )
    
    return fig

def create_score_radar(metrics: Dict[str, float], title: str = "Analysis Scores") -> go.Figure:
    """Create radar chart for multi-dimensional scoring"""
    categories = list(metrics.keys())
    values = list(metrics.values())
    
    # Close the radar chart
    categories += [categories[0]]
    values += [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Scores',
        line_color='#1f77b4'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title=title,
        height=400,
        template="plotly_white"
    )
    
    return fig

def create_timeline_chart(data: List[Dict[str, Any]], x_col: str, y_col: str, title: str) -> go.Figure:
    """Create time series chart"""
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df[x_col] = pd.to_datetime(df[x_col])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col.title(),
        yaxis_title=y_col.title(),
        height=400,
        template="plotly_white"
    )
    
    return fig

def create_sector_sentiment_chart(sector_data: Dict[str, float]) -> go.Figure:
    """Create horizontal bar chart for sector sentiment"""
    if not sector_data:
        return None
    
    sectors = list(sector_data.keys())
    sentiments = list(sector_data.values())
    
    # Color bars based on sentiment
    colors = [get_sentiment_color(sentiment) for sentiment in sentiments]
    
    fig = go.Figure(go.Bar(
        y=sectors,
        x=sentiments,
        orientation='h',
        marker_color=colors,
        text=[f"{sentiment:+.2f}" for sentiment in sentiments],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Sector Sentiment Breakdown",
        xaxis_title="Sentiment Score",
        yaxis_title="Sector",
        height=max(300, len(sectors) * 40),
        template="plotly_white"
    )
    
    return fig

def create_recommendation_distribution(recommendations: List[str]) -> go.Figure:
    """Create pie chart for recommendation distribution"""
    if not recommendations:
        return None
    
    # Count recommendations
    rec_counts = {}
    for rec in recommendations:
        rec_counts[rec] = rec_counts.get(rec, 0) + 1
    
    # Colors for recommendations
    colors = [get_recommendation_color(rec) for rec in rec_counts.keys()]
    
    fig = go.Figure(go.Pie(
        labels=list(rec_counts.keys()),
        values=list(rec_counts.values()),
        marker_colors=colors,
        textinfo='label+percent',
        hovertemplate='%{label}<br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Stock Recommendations Distribution",
        height=400,
        template="plotly_white"
    )
    
    return fig

def create_theme_frequency_chart(themes_data: List[Dict[str, Any]]) -> go.Figure:
    """Create horizontal bar chart for theme frequencies"""
    if not themes_data:
        return None
    
    df = pd.DataFrame(themes_data)
    df = df.sort_values('occurrence_count', ascending=True)
    
    # Color bars based on sentiment
    colors = [get_sentiment_color(sentiment) for sentiment in df['avg_sentiment']]
    
    fig = go.Figure(go.Bar(
        y=df['theme'],
        x=df['occurrence_count'],
        orientation='h',
        marker_color=colors,
        text=df['occurrence_count'],
        textposition='auto',
        hovertemplate='%{y}<br>Mentions: %{x}<br>Avg Sentiment: %{customdata:+.2f}<extra></extra>',
        customdata=df['avg_sentiment']
    ))
    
    fig.update_layout(
        title="Trending Financial Themes",
        xaxis_title="Occurrence Count",
        yaxis_title="Theme",
        height=max(400, len(themes_data) * 30),
        template="plotly_white"
    )
    
    return fig