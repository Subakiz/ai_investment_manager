"""
LQ45 stock symbols and market data utilities
"""

# LQ45 Index constituents (Top 45 liquid stocks on IDX)
# Updated as of August 2025 - these are the major Indonesian stocks
LQ45_STOCKS = [
    # Banking
    ("BBCA.JK", "Bank Central Asia Tbk"),
    ("BBRI.JK", "Bank Rakyat Indonesia Tbk"),
    ("BMRI.JK", "Bank Mandiri Tbk"),
    ("BBNI.JK", "Bank Negara Indonesia Tbk"),
    ("BBTN.JK", "Bank Tabungan Negara Tbk"),
    ("BRIS.JK", "Bank Syariah Indonesia Tbk"),
    
    # Telecommunications
    ("TLKM.JK", "Telkom Indonesia Tbk"),
    ("EXCL.JK", "XL Axiata Tbk"),
    ("ISAT.JK", "Indosat Ooredoo Hutchison Tbk"),
    
    # Consumer Goods
    ("UNVR.JK", "Unilever Indonesia Tbk"),
    ("INDF.JK", "Indofood Sukses Makmur Tbk"),
    ("ICBP.JK", "Indofood CBP Sukses Makmur Tbk"),
    ("KLBF.JK", "Kalbe Farma Tbk"),
    ("MYOR.JK", "Mayora Indah Tbk"),
    ("ULTJ.JK", "Ultra Jaya Milk Industry Tbk"),
    
    # Energy & Mining
    ("PTBA.JK", "Bukit Asam Tbk"),
    ("ADRO.JK", "Adaro Energy Tbk"),
    ("ITMG.JK", "Indo Tambangraya Megah Tbk"),
    ("PTRO.JK", "Petrosea Tbk"),
    ("MEDC.JK", "Medco Energi Internasional Tbk"),
    
    # Infrastructure & Transportation
    ("JSMR.JK", "Jasa Marga Tbk"),
    ("WIKA.JK", "Wijaya Karya Tbk"),
    ("WSKT.JK", "Waskita Karya Tbk"),
    ("PTPP.JK", "PP (Persero) Tbk"),
    
    # Property & Real Estate
    ("BSDE.JK", "Bumi Serpong Damai Tbk"),
    ("LPKR.JK", "Lippo Karawaci Tbk"),
    ("PWON.JK", "Pakuwon Jati Tbk"),
    ("SMRA.JK", "Summarecon Agung Tbk"),
    
    # Technology & E-commerce
    ("GOTO.JK", "GoTo Gojek Tokopedia Tbk"),
    ("BUKA.JK", "Bukalapak.com Tbk"),
    
    # Retail & Trade
    ("ACES.JK", "Ace Hardware Indonesia Tbk"),
    ("MAPI.JK", "Mitra Adiperkasa Tbk"),
    ("HERO.JK", "Hero Supermarket Tbk"),
    
    # Automotive
    ("ASII.JK", "Astra International Tbk"),
    ("AUTO.JK", "Astra Otoparts Tbk"),
    ("INDS.JK", "Indospring Tbk"),
    
    # Cement
    ("SMGR.JK", "Semen Indonesia Tbk"),
    ("INTP.JK", "Indocement Tunggal Prakasa Tbk"),
    
    # Pharmaceuticals
    ("KAEF.JK", "Kimia Farma Tbk"),
    ("PYFA.JK", "Pyridam Farma Tbk"),
    
    # Media & Entertainment
    ("SCMA.JK", "Surya Citra Media Tbk"),
    ("MNCN.JK", "Media Nusantara Citra Tbk"),
    
    # Agriculture & Food
    ("AALI.JK", "Astra Agro Lestari Tbk"),
    ("SIMP.JK", "Salim Ivomas Pratama Tbk"),
    ("LSIP.JK", "PP London Sumatra Indonesia Tbk"),
]

# Yahoo Finance suffix for Indonesian stocks
IDX_SUFFIX = ".JK"

def get_lq45_symbols() -> list[str]:
    """Get list of LQ45 stock symbols"""
    return [symbol for symbol, _ in LQ45_STOCKS]

def get_lq45_companies() -> dict[str, str]:
    """Get mapping of symbols to company names"""
    return {symbol: name for symbol, name in LQ45_STOCKS}

def format_idx_symbol(symbol: str) -> str:
    """Format symbol for Yahoo Finance (add .JK if not present)"""
    if not symbol.endswith(IDX_SUFFIX):
        symbol = f"{symbol}{IDX_SUFFIX}"
    return symbol

def clean_idx_symbol(symbol: str) -> str:
    """Remove .JK suffix from symbol"""
    return symbol.replace(IDX_SUFFIX, "")

# Market trading hours for IDX (Indonesian Stock Exchange)
IDX_MARKET_HOURS = {
    "open_time": "09:00",      # 9:00 AM WIB
    "close_time": "16:30",     # 4:30 PM WIB
    "timezone": "Asia/Jakarta",
    "trading_days": [0, 1, 2, 3, 4],  # Monday to Friday
}

# Data collection schedule (UTC times)
DATA_COLLECTION_SCHEDULE = {
    "market_data": "09:30",    # 4:30 PM WIB = 9:30 UTC
    "news_data": "09:45",      # 4:45 PM WIB = 9:45 UTC
}