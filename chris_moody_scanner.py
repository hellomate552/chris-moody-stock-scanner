import os
import sys
import glob
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import pandas as pd

# --- Base Directory Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

SCREENER_1_DIR = os.path.join(BASE_DIR, "Screener_1_With_Dollar1_Move")
SCREENER_2_DIR = os.path.join(BASE_DIR, "Screener_2_No_Dollar1_Limit")

def setup_logging():
    """Configures file and console logging."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "scanner.log")
    
    # Reset existing handlers to prevent duplicate log entries
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_us_eastern_datetime():
    """Gets the current date and time in US Eastern Time (America/New_York)."""
    return datetime.now(ZoneInfo('America/New_York'))

def is_us_weekend(ny_dt):
    """Returns True if it is Saturday (5) or Sunday (6) in US Eastern Time."""
    return ny_dt.weekday() in (5, 6)

def fetch_tradingview_data(require_dollar_move=True):
    """Queries TradingView's screener API with optional $1 move filter."""
    filter_label = "with >= $1 move filter" if require_dollar_move else "WITHOUT $1 move constraint"
    logging.info(f"Querying TradingView Screener API ({filter_label})...")
    
    url = "https://scanner.tradingview.com/america/scan"
    payload = {
        "filter": [
            {"left": "close", "operation": "in_range", "right": [3, 100]},
            {"left": "change", "operation": "in_range", "right": [4, 15]},
            {"left": "average_volume_10d_calc", "operation": "egreater", "right": 500000},
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"active_symbols_only": True},
        "markets": ["america"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "change", "average_volume_10d_calc", "open"],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 2000]
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Failed to fetch data from TradingView: {e}")
        return pd.DataFrame()
    
    results = []
    for item in data.get('data', []):
        d = item['d']
        ticker = d[0]
        close_price = d[1]
        change_pct = d[2]
        vol_10d = d[3]
        open_price = d[4]
        
        change_from_open_dollars = close_price - open_price
        
        # Filter condition based on require_dollar_move
        if not require_dollar_move or change_from_open_dollars >= 1.0:
            clean_ticker = ticker.split(':')[1] if ':' in ticker else ticker
            results.append({
                "Ticker": clean_ticker,
                "Close Price": close_price,
                "Change %": round(change_pct, 2),
                "10-Day Avg Vol": vol_10d,
                "Open Price": open_price,
                "Change from Open $": round(change_from_open_dollars, 2)
            })
            
    return pd.DataFrame(results)

def is_duplicate_data(df_today, all_files):
    """Compares today's scan with the most recent existing scan to check for market holiday/no-change."""
    if not all_files or df_today.empty:
        return False
    
    latest_file = all_files[0]
    try:
        df_prev = pd.read_excel(latest_file)
        if 'Ticker' in df_prev.columns and 'Close Price' in df_prev.columns:
            tickers_match = list(df_today['Ticker']) == list(df_prev['Ticker'])
            prices_match = list(df_today['Close Price']) == list(df_prev['Close Price'])
            if tickers_match and prices_match:
                logging.info(f"Fetched data matches previous scan ({os.path.basename(latest_file)}). Market closed (US Holiday).")
                return True
    except Exception as e:
        logging.warning(f"Could not read previous scan for duplicate check: {e}")
        
    return False

def process_screener(screener_name, screener_dir, require_dollar_move, ny_date_str):
    """Runs scanning, historical analysis, and watchlist generation for a given screener configuration."""
    logging.info(f"\n--- Running {screener_name} ---")
    
    scan_dir = os.path.join(screener_dir, "Chris_Moody_Daily_Scans")
    watchlist_dir = os.path.join(screener_dir, "Chris_Moody_Watchlists")
    
    os.makedirs(scan_dir, exist_ok=True)
    os.makedirs(watchlist_dir, exist_ok=True)
    
    daily_file_path = os.path.join(scan_dir, f"{ny_date_str}_Scan.xlsx")
    
    # 1. Same-Day Duplicate Check
    if os.path.exists(daily_file_path):
        logging.info(f"[{screener_name}] Today's scan ({ny_date_str}) already exists: {daily_file_path}. Skipping.")
        return

    # 2. Fetch TradingView Data
    df_today = fetch_tradingview_data(require_dollar_move=require_dollar_move)
    if df_today.empty:
        logging.warning(f"[{screener_name}] No stocks matched criteria or API request failed.")
        return

    # 3. US Market Holiday Guard
    existing_files = glob.glob(os.path.join(scan_dir, "*_Scan.xlsx"))
    existing_files.sort(reverse=True)
    
    if is_duplicate_data(df_today, existing_files):
        logging.info(f"[{screener_name}] Skipping file creation to avoid duplicate market data on non-trading day/holiday.")
        return

    # 4. Save Today's Scan
    df_today.to_excel(daily_file_path, index=False)
    logging.info(f"[{screener_name}] Saved {len(df_today)} stocks to {daily_file_path}")

    # 5. Process Historical Daily Scans
    all_files = glob.glob(os.path.join(scan_dir, "*_Scan.xlsx"))
    all_files.sort(reverse=True)
    
    recent_files = all_files[:40]
    logging.info(f"[{screener_name}] Analyzing {len(recent_files)} historical daily scans...")
    
    tickers_list = []
    for file in recent_files:
        try:
            temp_df = pd.read_excel(file)
            if 'Ticker' in temp_df.columns:
                tickers_list.extend(temp_df['Ticker'].tolist())
        except Exception as e:
            logging.warning(f"[{screener_name}] Failed to read file {file}: {e}")
            
    if not tickers_list:
        logging.warning(f"[{screener_name}] No historical tickers found to build watchlist.")
        return

    # 6. Occurrence Count & Dynamic Threshold (25%)
    counts = pd.Series(tickers_list).value_counts().reset_index()
    counts.columns = ['Ticker', 'Occurrences']
    
    threshold = max(1, int(len(recent_files) * 0.25))
    logging.info(f"[{screener_name}] Dynamic Threshold Applied: Needs >= {threshold} occurrences (out of {len(recent_files)} days)")
    
    final_watchlist = counts[counts['Occurrences'] >= threshold]
    
    # 7. Save Watchlist Excel
    watchlist_file_path = os.path.join(watchlist_dir, f"{ny_date_str}_Watchlist.xlsx")
    final_watchlist.to_excel(watchlist_file_path, index=False)
    logging.info(f"[{screener_name}] Saved Watchlist with {len(final_watchlist)} stocks to {watchlist_file_path}")

    # 8. Save TradingView Importable Watchlist (.txt)
    tv_txt_path = os.path.join(watchlist_dir, f"{ny_date_str}_TradingView_Watchlist.txt")
    with open(tv_txt_path, "w", encoding="utf-8") as f:
        f.write(", ".join(final_watchlist['Ticker'].tolist()))
    logging.info(f"[{screener_name}] Saved TradingView importable text watchlist to {tv_txt_path}")

def run_all_screeners():
    setup_logging()
    
    ny_dt = get_us_eastern_datetime()
    ny_date_str = ny_dt.strftime("%Y-%m-%d")
    ny_time_str = ny_dt.strftime("%H:%M:%S")
    
    logging.info("==================================================")
    logging.info(f"=== Dual Chris Moody Stock Scanner Started ===")
    logging.info(f"Current US Eastern Time (NY): {ny_date_str} {ny_time_str} EDT/EST")
    logging.info("==================================================")
    
    # Weekend Check based on US Eastern Time
    if is_us_weekend(ny_dt):
        logging.info(f"Today ({ny_date_str}) is a Weekend in the USA (Saturday/Sunday). Stock market is closed. Exiting.")
        return

    # Screener 1: Require >= $1.00 move from Open
    process_screener(
        screener_name="Screener 1 (With $1 Move)",
        screener_dir=SCREENER_1_DIR,
        require_dollar_move=True,
        ny_date_str=ny_date_str
    )

    # Screener 2: Do NOT require $1.00 move from Open
    process_screener(
        screener_name="Screener 2 (No $1 Move Limit)",
        screener_dir=SCREENER_2_DIR,
        require_dollar_move=False,
        ny_date_str=ny_date_str
    )

    logging.info("\n=== All Screeners Completed Successfully ===")

if __name__ == "__main__":
    run_all_screeners()
