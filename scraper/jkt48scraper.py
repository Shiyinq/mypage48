"""Main JKT48 Scraper module."""
import argparse
import asyncio
import json
import os
import sys

# Change working directory to the script's directory
# This ensures relative paths (data/, cookies.json, etc.) work correctly
# regardless of where the script is executed from.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List, Optional, Union

from src.news import get_news_page, get_news, get_all_news
from src.schedule import get_calendar_events_by_url
from src.theater import get_theater_detail
from src.schedule import get_calendar_events_by_url
from src.theater import get_theater_detail
from src.setlist import fetch_all_setlists_with_songs_and_lyrics
from src.agent.cookies import get_cookies_headers as get_jkt48_headers
from src.utils import get_theater_id
from src.merger import merge_data


def fetch_news_data() -> List[Dict[str, Any]]:
    """Fetch and store JKT48 news."""
    headers = get_jkt48_headers()
    news_list = get_news_page(1, None, headers)
    
    results = []
    for news in news_list:
        # Check if news already exists (implement your own logic)
        # if news_exists(news['id']):
        #     continue
        
        time.sleep(0.35)  # Rate limiting
        print(f"Processing: {news.get('date', 'Unknown Date')} - {news.get('title', 'Unknown Title')}")
        news_detail = get_news(news['id'], headers)
        news_data = {
            **news_detail,
            'label': news['label'],
        }
        results.append(news_data)
        
        # Save to database (implement your own logic)
        # save_news(news_data)
    
    return results


def fetch_schedule_data() -> Dict[str, List]:
    """Fetch and store JKT48 schedules."""
    now = datetime.now()
    next_month = now + relativedelta(months=1)
    headers = get_jkt48_headers()
    
    # Fetch current and next month schedules
    schedules = []
    
    current_month_url = f'/calendar/list/y/{now.year}/m/{now.month}/d/1'
    next_month_url = f'/calendar/list/y/{next_month.year}/m/{next_month.month}/d/1'
    
    schedules.extend(get_calendar_events_by_url(current_month_url, 0, headers))
    schedules.extend(get_calendar_events_by_url(next_month_url, 0, headers))
    
    return process_schedules(schedules, headers)


def process_schedules(schedules: List[Dict[str, Any]], headers: Dict[str, str]) -> Dict[str, List]:
    """Process raw schedules to get detailed events and members."""
    results = {
        'events': [],
        'members': [],
    }
    
    for schedule in schedules:
        # Save schedule (implement your own logic)
        # save_schedule(schedule)
        
        # If it's a theater schedule, fetch theater details
        if schedule['url'].startswith('/theater/schedule/id'):
            theater_id = get_theater_id(schedule['url'])
            if theater_id:
                time.sleep(0.35)  # Rate limiting
                theater_data = get_theater_detail(theater_id, 0, headers)
                
                # Save members
                for member in theater_data['members']:
                    # save_member(member)
                    results['members'].append(member)
                
                # Save theater shows
                for theater_detail in theater_data['show']:
                    # save_theater(theater_detail)
                    theater_detail['label'] = schedule.get('label', '')
                    results['events'].append(theater_detail)
        else:
            # If it's not a theater schedule (e.g. event), just append it to events
            results['events'].append(schedule)
    
    return results


def fetch_setlist_data() -> List[Dict[str, Any]]:
    """Fetch all setlists with songs and lyrics."""
    headers = get_jkt48_headers()
    return fetch_all_setlists_with_songs_and_lyrics(headers)


def _json_serializer(obj):
    """Handle datetime serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _ensure_data_folder():
    """Create data folder if not exists."""
    os.makedirs('data', exist_ok=True)


def run_setlist_scraper():
    """Fetch and save setlists to JSON file."""
    _ensure_data_folder()
    
    print('\n=== Fetching Setlists ===')
    setlists = fetch_setlist_data()
    print(f'Got {len(setlists)} setlists')
    
    with open('data/setlists.json', 'w', encoding='utf-8') as f:
        json.dump(setlists, f, default=_json_serializer, ensure_ascii=False, indent=2)
    print('Saved: data/setlists.json')
    
    return setlists


def run_news_scraper():
    """Fetch and save news to JSON file."""
    _ensure_data_folder()
    
    print('\n=== Fetching News ===')
    news = fetch_news_data()
    print(f'Got {len(news)} news items')
    
    with open('data/news.current.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, default=_json_serializer, ensure_ascii=False, indent=2)
    print('Saved: data/news.current.json')
    
    return news


def run_schedule_scraper():
    """Fetch and save schedules (events) to JSON files."""
    _ensure_data_folder()
    
    print('\n=== Fetching Schedule ===')
    result = fetch_schedule_data()
    print(f'Got {len(result["events"])} events')
    
    with open('data/events.current.json', 'w', encoding='utf-8') as f:
        json.dump(result['events'], f, default=_json_serializer, ensure_ascii=False, indent=2)
    print('Saved: data/events.current.json')
    
    return result


def run_historical_schedule_scraper(year: int):
    """Fetch and save historical schedules for a specific year."""
    # Ensure folder data/schedule exists
    output_dir = 'data/schedule'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f'\n=== Fetching Historical Schedule for {year} ===')
    # We can reuse fetch_schedule_data but we need to inject year-month logic
    # Actually, fetch_schedule_data gets current/next month.
    # We need a function to fetch ALL months for a given year.
    
    headers = get_jkt48_headers()
    schedules = []
    
    # Iterate months 1-12
    for month in range(1, 13):
        url = f'/calendar/list/y/{year}/m/{month}/d/1'
        print(f"Fetching {year}-{month}...")
        try:
            events = get_calendar_events_by_url(url, 0, headers)
            schedules.extend(events)
            time.sleep(0.5) # Be nice
        except Exception as e:
            print(f"Error fetching {year}-{month}: {e}")

    # Process details (theater etc)
    print("Processing detailed events...")
    # NOTE: process_schedules expects a list of event dictionaries
    # But get_calendar_events_by_url returns processed events (dictionaries) ?
    # Let's check src/schedule.py: get_calendar_events_by_url returns List[Dict]
    # process_schedules in scraper.py: iterates and fetches theater details if needed
    
    result = process_schedules(schedules, headers)
    
    # Save to data/schedule/events.schedule.{year}.json
    filename = f'events.schedule.{year}.json'
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, default=_json_serializer, ensure_ascii=False, indent=2)
        
    print(f'Saved: {filepath}')
    return result


# ============ Main Entry Point ============

if __name__ == '__main__':
    """Run scrapers based on CLI flags."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='JKT48 Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''

  python jkt48scraper.py --setlist      # Run setlist scraper only
  python jkt48scraper.py --news         # Run news scraper (fetch latest news from page 1)
  python jkt48scraper.py --schedule     # Run schedule scraper (current & next month)
  python jkt48scraper.py --schedule 2011       # Run schedule scraper for specific year
  python jkt48scraper.py --schedule 2011-2023  # Run schedule scraper for range of years
        '''
    )
    

    parser.add_argument('--setlist', action='store_true', help='Run setlist scraper')
    parser.add_argument('--news', action='store_true', help='Run news scraper (fetch latest news from page 1)')
    parser.add_argument('--schedule', nargs='?', const='current', help='Run schedule scraper (optional: year or range)')
    parser.add_argument('--merge', action='store_true', help='Merge historical schedule data (use with --schedule)')
    parser.add_argument('--schedule-merge', action='store_true', help='Run merge process for historical schedule data only')
    
    args = parser.parse_args()
    
    # Check if at least one flag is provided
    if not (args.setlist or args.news or args.schedule or args.schedule_merge):
        parser.print_help()
        print('\nError: At least one flag is required!')
        exit(1)
    
    print('Starting JKT48 scraper...')
    
    if args.setlist:
        run_setlist_scraper()
    if args.news:
        run_news_scraper()
    if args.schedule:
        if args.schedule == 'current':
            run_schedule_scraper()
        else:
            if '-' in args.schedule:
                start_year, end_year = map(int, args.schedule.split('-'))
                for year in range(start_year, end_year + 1):
                    run_historical_schedule_scraper(year)
            else:
                run_historical_schedule_scraper(int(args.schedule))
            
            # If --merge flag is present and we processed historical data
            if args.merge:
                print('\n=== Running Data Merge ===')
                merge_data()

    if args.schedule_merge:
        print('\n=== Running Data Merge ===')
        merge_data()
    
    print('\nDone!')
