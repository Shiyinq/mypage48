"""Schedule/Calendar scraper for JKT48 website."""
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from tqdm import tqdm

from .utils import extract_year_and_month_from_url
from .agent.browser import request


def get_all_calendar(headers: Optional[Dict[str, str]] = None) -> List[str]:
    """Get all calendar month URLs."""
    response = request(
        'GET',
        'https://jkt48.com/calendar/list/',
        headers=headers or {},
        impersonate='chrome'
    )
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    months_data = soup.select('.entry-schedule__footer .entry-schedule__footer--month a')
    
    urls = [a.get('href') for a in months_data if a.get('href')]
    return sorted(urls, reverse=True)


def get_all_calendar_events(headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """Get all calendar events from all months."""
    months = get_all_calendar(headers)
    events = []
    
    for url in tqdm(months, desc="Fetching calendar"):
        time.sleep(0.1)
        data = get_calendar_events_by_url(url, 0, headers)
        events.extend(data)
    
    return events


def get_events(body: str, url: str) -> List[Dict[str, Any]]:
    """Parse events from HTML body."""
    soup = BeautifulSoup(body, 'html.parser')
    items = soup.select('table tbody tr')
    
    events = []
    year, month = extract_year_and_month_from_url(f'https://jkt48.com{url}')
    
    for event in items:
        date_td = event.select_one('td:nth-child(1)')
        date_string = 1
        if date_td:
            # Extract number from text like "1(Kamis)" or just "1"
            match = re.match(r'(\d+)', date_td.get_text(strip=True))
            if match:
                date_string = int(match.group(1))
        
        if year and month:
            date = datetime(year, month, date_string)
        else:
            date = datetime.now()
        
        for content in event.select('td .contents'):
            title_text = content.get_text(strip=True).lower().replace(' ', '-')
            event_id = f"{date.strftime('%Y%m%d')}-{title_text}"
            
            img_el = content.select_one('img')
            link_el = content.select_one('a')
            
            events.append({
                'id': event_id,
                'label': img_el.get('src', '') if img_el else '',
                'title': content.get_text(strip=True),
                'url': link_el.get('href', '') if link_el else '',
                'date': date,
            })
    
    return events


def get_calendar_events_by_url(
    url: str,
    retry: int = 0,
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Get calendar events by URL with retry logic."""
    try:
        response = request(
            'GET',
            f'https://jkt48.com{url}',
            headers=headers or {},
            impersonate='chrome'
        )
        response.raise_for_status()
        
        return get_events(response.text, url)
    
    except Exception as e:
        if retry > 10:
            raise e
        time.sleep(0.3)
        return get_calendar_events_by_url(url, retry + 1, headers)


def get_calendar_events(
    date: datetime,
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Get calendar events for a specific month."""
    url = f'/calendar/list/y/{date.year}/m/{date.month}/d/1'
    
    response = request(
        'GET',
        f'https://jkt48.com{url}',
        headers=headers or {},
        impersonate='chrome'
    )
    response.raise_for_status()
    
    return get_events(response.text, url)
