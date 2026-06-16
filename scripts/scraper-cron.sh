#!/usr/bin/env bash
# MyPage48 Daily Scraper Cron Loop

# Ensure log directory exists
mkdir -p /var/log/mypage48

# Redirect all stdout/stderr to log file for both cron and manual runs within this script
exec > >(tee -a /var/log/mypage48/scraper.log) 2>&1

echo "$(date): Starting Scraper Cron Loop..."

# --- INITIAL RUN ---
# Run once at startup to ensure data is fresh and skip waiting for midnight
echo "$(date): Performing initial scraper run..."
python scraper/jkt48scraper.py --schedule --sync
python scraper/jkt48scraper.py --news --sync
echo "$(date): Initial run complete. Entering scheduled loop."

while true; do
  # Get current hour and minute
  export CURRENT_HOUR=$(date +%H)
  export CURRENT_MIN=$(date +%M)

  # Check if it is midnight (00:00 to 00:05)
  if [ "$CURRENT_HOUR" == "00" ] && [ "$CURRENT_MIN" -le "05" ]; then
    echo "$(date): Running scheduled JKT48 Scraper..."
    
    # Run Schedule Sync
    echo "Syncing Schedules..."
    python scraper/jkt48scraper.py --schedule --sync
    
    # Run News Sync
    echo "Syncing News..."
    python scraper/jkt48scraper.py --news --sync
    
    echo "Scraper run complete. Sleeping for 1 hour to avoid double run."
    sleep 3600
  fi
  
  # Check every minute
  sleep 60
done
