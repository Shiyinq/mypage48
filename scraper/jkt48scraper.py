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
from src.schedule import get_schedules_by_month, get_theater_or_event_detail
from src.members import fetch_and_format_members
from src.setlist import fetch_all_setlists_with_songs_and_lyrics
from src.agent.cookies import get_cookies_headers as get_jkt48_headers
from src.utils import get_theater_id
from src.merger import merge_data


def fetch_news_data(pages: str = "1") -> List[Dict[str, Any]]:
    """Fetch and store JKT48 news with pagination support."""
    headers = get_jkt48_headers()
    news_list = []
    
    if pages == "all":
        print("Fetching all news pages...")
        news_list = get_all_news(1, None, headers)
    elif "-" in pages:
        try:
            start_p, end_p = map(int, pages.split("-"))
            for p in range(start_p, end_p + 1):
                print(f"Fetching news page {p}...")
                news_list.extend(get_news_page(p, None, headers))
                time.sleep(0.35)
        except ValueError:
            print(f"Invalid range format: {pages}. Defaulting to page 1.")
            news_list = get_news_page(1, None, headers)
    else:
        try:
            p = int(pages)
            news_list = get_news_page(p, None, headers)
        except ValueError:
            news_list = get_news_page(1, None, headers)
    
    results = []
    print(f"Found {len(news_list)} news items. Fetching details...")
    for news in news_list:
        time.sleep(0.35)  # Rate limiting
        print(f"Processing: {news.get('date', 'Unknown Date')} - {news.get('title', 'Unknown Title')}")
        news_detail = get_news(news.get('link'), headers)
        
        news_data = {
            **news,
            **news_detail,
        }
        results.append(news_data)
    
    return results


def fetch_members_data() -> List[Dict[str, Any]]:
    """Fetch and store JKT48 members (delegated to src.members)."""
    headers = get_jkt48_headers()
    return fetch_and_format_members(headers)


def fetch_schedule_data() -> Dict[str, List]:
    """Fetch and store JKT48 schedules."""
    now = datetime.now()
    next_month = now + relativedelta(months=1)
    headers = get_jkt48_headers()
    
    schedules = []
    
    schedules.extend(get_schedules_by_month(now.year, now.month, headers))
    schedules.extend(get_schedules_by_month(next_month.year, next_month.month, headers))
    
    return process_schedules(schedules, headers)


def process_schedules(schedules: List[Dict[str, Any]], headers: Dict[str, str]) -> Dict[str, List]:
    """Process raw schedules to get detailed events and members."""
    results = {
        'events': [],
        'members': [],
    }
    
    for schedule in schedules:
        ref_code = schedule['id']
        event_type = schedule.get('type', 'EVENT')
        
        time.sleep(0.35)  # Rate limiting
        print(f"Fetching detail for {event_type} {ref_code}")
        detail_data = get_theater_or_event_detail(ref_code, event_type, 1, headers)
        
        if detail_data and detail_data.get('show'):
            # Save members
            for member in detail_data['members']:
                results['members'].append(member)
            
            # Save theater/event shows
            for detail_event in detail_data['show']:
                detail_event['raw_data']['short'] = schedule.get('raw_data', {}).get('short', {})
                detail_event['label'] = schedule.get('label', '')
                detail_event['type'] = event_type
                results['events'].append(detail_event)
        else:
            # If detail fetch failed or returned empty
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


def run_members_scraper():
    """Fetch and save members to JSON file."""
    _ensure_data_folder()
    
    print('\n=== Fetching Members ===')
    members = fetch_members_data()
    print(f'Got {len(members)} members')
    
    with open('data/members.current.json', 'w', encoding='utf-8') as f:
        json.dump(members, f, default=_json_serializer, ensure_ascii=False, indent=2)
    print('Saved: data/members.current.json')
    
    return members


def run_news_scraper(pages: str = "1"):
    """Fetch and save news to JSON file with pagination support."""
    _ensure_data_folder()
    
    print('\n=== Fetching News ===')
    news = fetch_news_data(pages)
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
        print(f"Fetching {year}-{month}...")
        try:
            events = get_schedules_by_month(year, month, headers)
            schedules.extend(events)
            time.sleep(0.5) # Be nice
        except Exception as e:
            print(f"Error fetching {year}-{month}: {e}")

    # Process details (theater etc)
    print("Processing detailed events...")
    
    result = process_schedules(schedules, headers)
    
    # Save to data/schedule/events.schedule.{year}.json
    filename = f'events.schedule.{year}.json'
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, default=_json_serializer, ensure_ascii=False, indent=2)
        
    print(f'Saved: {filepath}')
    return result


# Main Entry Point

if __name__ == '__main__':
    """Run scrapers based on CLI flags."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='JKT48 Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''

  python jkt48scraper.py --setlist      # Run setlist scraper only
  python jkt48scraper.py --members      # Run members scraper only
  python jkt48scraper.py --news         # Run news scraper (default: page 1)
  python jkt48scraper.py --news 5       # Run news scraper for specific page
  python jkt48scraper.py --news 1-10    # Run news scraper for pages 1 to 10
  python jkt48scraper.py --news all     # Run news scraper for all available pages
  python jkt48scraper.py --schedule     # Run schedule scraper (default: current & next month)
  python jkt48scraper.py --schedule 2011       # Run schedule scraper for specific year
  python jkt48scraper.py --schedule 2011-2023  # Run schedule scraper for range of years
  python jkt48scraper.py --schedule all        # Run schedule scraper for all years (2011-present)
        '''
    )
    

    parser.add_argument('--setlist', action='store_true', help='Run setlist scraper')
    parser.add_argument('--news', nargs='?', const='1', metavar='PAGE', help='Run news scraper (optional: page, range 1-10, or all)')
    parser.add_argument('--members', action='store_true', help='Run members scraper')
    parser.add_argument('--schedule', nargs='?', const='current', metavar='YEAR', help='Run schedule scraper (optional: year, range 2011-2023, all, or current)')
    parser.add_argument('--merge', action='store_true', help='Merge historical schedule data (use with --schedule)')
    parser.add_argument('--schedule-merge', action='store_true', help='Run merge process for historical schedule data only')
    
    args = parser.parse_args()
    
    if not (args.setlist or args.news or args.members or args.schedule or args.schedule_merge):
        parser.print_help()
        print('\nError: At least one flag is required!')
        exit(1)
    
    print('Starting JKT48 scraper...')
    
    if args.setlist:
        run_setlist_scraper()
    if args.news:
        run_news_scraper(args.news)
    if args.members:
        run_members_scraper()
    if args.schedule:
        if args.schedule == 'current':
            run_schedule_scraper()
        elif args.schedule == 'all':
            start_year = 2011
            end_year = datetime.now().year
            for year in range(start_year, end_year + 1):
                run_historical_schedule_scraper(year)
            
            if args.merge:
                print('\n=== Running Data Merge ===')
                merge_data()
        else:
            if '-' in args.schedule:
                start_year, end_year = map(int, args.schedule.split('-'))
                for year in range(start_year, end_year + 1):
                    run_historical_schedule_scraper(year)
            else:
                run_historical_schedule_scraper(int(args.schedule))
            
            if args.merge:
                print('\n=== Running Data Merge ===')
                merge_data()

    if args.schedule_merge:
        print('\n=== Running Data Merge ===')
        merge_data()
    
    print('\nDone!')
