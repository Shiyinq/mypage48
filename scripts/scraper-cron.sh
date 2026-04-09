#!/usr/bin/env bash
# MyPage48 Daily Scraper Cron Loop

echo "Starting Scraper Cron Loop..."

while true; do
  # Get current hour and minute
  export CURRENT_HOUR=$(date +%H)
  export CURRENT_MIN=$(date +%M)

  # Check if it is midnight (00:00 to 00:05)
  if [ "$CURRENT_HOUR" == "00" ] && [ "$CURRENT_MIN" -le "05" ]; then
    echo "$(date): Running scheduled JKT48 Scraper..."
    
    # Run Schedule Sync
    echo "Syncing Schedules..."
    python src/scraper/jkt48scraper.py --schedule --sync
    
    # Run News Sync
    echo "Syncing News..."
    python src/scraper/jkt48scraper.py --news --sync
    
    echo "Scraper run complete. Sleeping for 1 hour to avoid double run."
    sleep 3600
  fi
  
  # Check every minute
  sleep 60
done
