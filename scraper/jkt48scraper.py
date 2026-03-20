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
from abc import ABC, abstractmethod
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List, Optional, Union

from src.news import get_news_page, get_news, get_all_news
from src.schedule import get_schedules_by_month, get_theater_or_event_detail
from src.members import fetch_and_format_members
from src.agent.cookies import get_cookies_headers as get_jkt48_headers
from src.utils import get_theater_id
from src.merger import merge_data
from src.db import MongoDB, upsert_data


# ──────────────────────────────────────────────
# Data Fetching Functions (Business Logic)
# ──────────────────────────────────────────────

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
        time.sleep(0.35)
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
        
        time.sleep(0.35)
        print(f"Fetching detail for {event_type} {ref_code}")
        detail_data = get_theater_or_event_detail(ref_code, event_type, 1, headers)
        
        if detail_data and detail_data.get('show'):
            for member in detail_data['members']:
                results['members'].append(member)
            
            for detail_event in detail_data['show']:
                detail_event['raw_data']['short'] = schedule.get('raw_data', {}).get('short', {})
                detail_event['label'] = schedule.get('label', '')
                detail_event['type'] = event_type
                results['events'].append(detail_event)
        else:
            results['events'].append(schedule)
            
    return results



# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────

def _json_serializer(obj):
    """Handle datetime serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ──────────────────────────────────────────────
# Template Method Pattern: BaseScraper
# ──────────────────────────────────────────────

class BaseScraper(ABC):
    """Base scraper using Template Method pattern.
    
    Template: run() defines the fixed algorithm:
        1. Prepare (ensure folders)
        2. Fetch data (subclass defines HOW)
        3. Save to JSON
        4. Optionally sync to MongoDB
    
    Subclasses only need to define:
        - name: display name
        - output_file: JSON output path
        - collection_name: MongoDB collection
        - id_field: unique identifier field for upsert
        - fetch(): how to get the data
    """
    
    name: str = ""
    output_file: str = ""
    collection_name: str = ""
    id_field: str = "id"
    
    def run(self, sync_db: bool = False):
        """Template method — the fixed algorithm."""
        self._prepare()
        self._print_header()
        data = self.fetch()
        self._print_count(data)
        self.save(data)
        if sync_db:
            self.sync(data)
        return data
    
    @abstractmethod
    def fetch(self):
        """Fetch data — subclass must implement."""
        pass
    
    def save(self, data):
        """Save data to JSON file."""
        items = self._get_items(data)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, default=_json_serializer, ensure_ascii=False, indent=2)
        print(f'Saved: {self.output_file}')
    
    def sync(self, data):
        """Sync data to MongoDB."""
        items = self._get_items(data)
        print(f"\n🔌 Syncing {self.name.lower()} to MongoDB...")
        db = MongoDB()
        if db.connect():
            stats = upsert_data(db.get_collection(self.collection_name), items, id_field=self.id_field)
            print(f"✅ Sync result: {stats['inserted']} inserted, {stats['updated']} updated")
            db.close()
    
    def _prepare(self):
        """Ensure output directories exist."""
        output_dir = os.path.dirname(self.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
    
    def _print_header(self):
        print(f'\n=== Fetching {self.name} ===')
    
    def _print_count(self, data):
        items = self._get_items(data)
        print(f'Got {len(items)} {self.name.lower()}')
    
    def _get_items(self, data):
        """Extract the list of items from data. Override if data is a dict."""
        return data


# ──────────────────────────────────────────────
# Concrete Scrapers
# ──────────────────────────────────────────────

class MembersScraper(BaseScraper):
    name = "Members"
    output_file = "data/members.current.json"
    collection_name = "members"
    
    def fetch(self):
        return fetch_members_data()


class NewsScraper(BaseScraper):
    name = "News"
    output_file = "data/news.current.json"
    collection_name = "news"
    id_field = "news_id"
    
    def __init__(self, pages: str = "1"):
        self.pages = pages
    
    def fetch(self):
        return fetch_news_data(self.pages)


class ScheduleScraper(BaseScraper):
    name = "Schedule"
    output_file = "data/events.current.json"
    collection_name = "events"
    
    def fetch(self):
        return fetch_schedule_data()
    
    def _get_items(self, data):
        """Schedule returns {'events': [...], 'members': [...]}."""
        if isinstance(data, dict):
            return data.get('events', [])
        return data
    
    def sync(self, data):
        """Sync events and involved members."""
        super().sync(data)
        if isinstance(data, dict) and data.get('members'):
            print("🔌 Syncing involved members to MongoDB...")
            db = MongoDB()
            if db.connect():
                m_stats = upsert_data(db.get_collection('members'), data['members'])
                print(f"✅ Sync result (members): {m_stats['inserted']} inserted, {m_stats['updated']} updated")
                db.close()


class HistoricalScheduleScraper(BaseScraper):
    name = "Historical Schedule"
    collection_name = "events"
    
    def __init__(self, year: int):
        self.year = year
        self.output_file = f"data/schedule/events.schedule.{year}.json"
    
    def fetch(self):
        headers = get_jkt48_headers()
        schedules = []
        
        for month in range(1, 13):
            print(f"Fetching {self.year}-{month}...")
            try:
                events = get_schedules_by_month(self.year, month, headers)
                schedules.extend(events)
                time.sleep(0.5)
            except Exception as e:
                print(f"Error fetching {self.year}-{month}: {e}")

        print("Processing detailed events...")
        return process_schedules(schedules, headers)
    
    def _print_header(self):
        print(f'\n=== Fetching Historical Schedule for {self.year} ===')
    
    def _get_items(self, data):
        if isinstance(data, dict):
            return data.get('events', [])
        return data
    
    def save(self, data):
        """Save full result (events + members) for historical data."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=_json_serializer, ensure_ascii=False, indent=2)
        print(f'Saved: {self.output_file}')
    
    def sync(self, data):
        """Sync events and involved members."""
        print(f"\n🔌 Syncing {self.year} events to MongoDB...")
        db = MongoDB()
        if db.connect():
            stats = upsert_data(db.get_collection(self.collection_name), self._get_items(data))
            print(f"✅ Sync result (events): {stats['inserted']} inserted, {stats['updated']} updated")
            
            if isinstance(data, dict) and data.get('members'):
                print("🔌 Syncing involved members to MongoDB...")
                m_stats = upsert_data(db.get_collection('members'), data['members'])
                print(f"✅ Sync result (members): {m_stats['inserted']} inserted, {m_stats['updated']} updated")
            
            db.close()



# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='JKT48 Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''

  python jkt48scraper.py --members      # Run members scraper only
  python jkt48scraper.py --news         # Run news scraper (default: page 1)
  python jkt48scraper.py --news 5       # Run news scraper for specific page
  python jkt48scraper.py --news 1-10    # Run news scraper for pages 1 to 10
  python jkt48scraper.py --news all     # Run news scraper for all available pages
  python jkt48scraper.py --schedule     # Run schedule scraper (default: current & next month)
  python jkt48scraper.py --schedule 2011       # Run schedule scraper for specific year
  python jkt48scraper.py --schedule 2011-2023  # Run schedule scraper for range of years
  python jkt48scraper.py --schedule all        # Run schedule scraper for all years (2011-present)
  python jkt48scraper.py --news --sync         # Fetch news and sync to MongoDB
  python jkt48scraper.py --members --sync      # Fetch members and sync to MongoDB
  python jkt48scraper.py --schedule --sync     # Fetch schedule and sync to MongoDB
        '''
    )
    
    parser.add_argument('--news', nargs='?', const='1', metavar='PAGE', help='Run news scraper (optional: page, range 1-10, or all)')
    parser.add_argument('--members', action='store_true', help='Run members scraper')
    parser.add_argument('--schedule', nargs='?', const='current', metavar='YEAR', help='Run schedule scraper (optional: year, range 2011-2023, all, or current)')
    parser.add_argument('--merge', action='store_true', help='Merge historical schedule data (use with --schedule)')
    parser.add_argument('--schedule-merge', action='store_true', help='Run merge process for historical schedule data only')
    parser.add_argument('--sync', action='store_true', help='Sync fetched data to MongoDB')
    
    args = parser.parse_args()
    
    if not (args.news or args.members or args.schedule or args.schedule_merge):
        parser.print_help()
        print('\nError: At least one flag is required!')
        exit(1)
    
    print('Starting JKT48 scraper...')
    
    if args.news:
        NewsScraper(args.news).run(args.sync)
    
    if args.members:
        MembersScraper().run(args.sync)
    
    if args.schedule:
        if args.schedule == 'current':
            ScheduleScraper().run(args.sync)
        elif args.schedule == 'all':
            start_year = 2011
            end_year = datetime.now().year
            for year in range(start_year, end_year + 1):
                HistoricalScheduleScraper(year).run(args.sync)
            
            if args.merge:
                print('\n=== Running Data Merge ===')
                merge_data()
        else:
            if '-' in args.schedule:
                start_year, end_year = map(int, args.schedule.split('-'))
                for year in range(start_year, end_year + 1):
                    HistoricalScheduleScraper(year).run(args.sync)
            else:
                HistoricalScheduleScraper(int(args.schedule)).run(args.sync)
            
            if args.merge:
                print('\n=== Running Data Merge ===')
                merge_data()

    if args.schedule_merge:
        print('\n=== Running Data Merge ===')
        merge_data()
    
    print('\nDone!')
