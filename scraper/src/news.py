"""News scraper for JKT48 website."""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .utils import extract_news_id
from .agent.browser import request

BASE_URL = 'https://jkt48.com/news/list'


async def sleep(ms: int):
    """Sleep for specified milliseconds."""
    await asyncio.sleep(ms / 1000)


def get_news_page(
    page: int = 1,
    news: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Get news from a single page."""
    if news is None:
        news = []
    
    response = request(
        'GET',
        f'{BASE_URL}?page={page}&lang=id',
        headers=headers or {},
        impersonate='chrome'
    )
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    news_elements = soup.select('.entry-news .entry-news__list')
    
    for n in news_elements:
        time_el = n.select_one('time')
        date_string = time_el.get_text(strip=True) if time_el else ''
        
        link_el = n.select_one('div h3 a')
        img_el = n.select_one('img')
        
        href = link_el.get('href', '') if link_el else ''
        
        news.append({
            'id': extract_news_id(href) or '0',
            'label': img_el.get('src', '') if img_el else '',
            'title': link_el.get_text(strip=True) if link_el else '',
            'url': href,
            'date': parse_date(date_string),
        })
    
    return sorted(news, key=lambda x: int(x['id']))


def get_all_news(
    page: int = 1,
    news: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Get all news with pagination."""
    if news is None:
        news = []
    
    response = request_with_retry(
        'GET',
        f'{BASE_URL}?page={page}&lang=id',
        headers=headers or {},
        impersonate='chrome'
    )
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    news_elements = soup.select('.entry-news .entry-news__list')
    pagination = soup.select_one('.entry-news .entry-news__list--pagination')
    
    for n in news_elements:
        time_el = n.select_one('time')
        date_string = time_el.get_text(strip=True) if time_el else ''
        
        link_el = n.select_one('div h3 a')
        img_el = n.select_one('img')
        
        href = link_el.get('href', '') if link_el else ''
        
        news.append({
            'id': extract_news_id(href) or '0',
            'label': img_el.get('src', '') if img_el else '',
            'title': link_el.get_text(strip=True) if link_el else '',
            'url': href,
            'date': parse_date(date_string),
        })
    
    # Check for next page
    if pagination and pagination.select_one('.next a'):
        return get_all_news(page + 1, news, headers)
    
    return sorted(news, key=lambda x: int(x['id']))


def get_news(news_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get single news detail."""
    url = f'https://jkt48.com/news/detail/id/{news_id}?lang=id'
    
    response = request('GET', url, headers=headers or {}, impersonate='chrome')
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    content_el = soup.select_one('.entry-news .entry-news__detail div:last-child')
    date_el = soup.select_one('.entry-news .entry-news__detail div')
    title_el = soup.select_one('.entry-news .entry-news__detail h3')
    
    content = str(content_el) if content_el else ''
    date_text = date_el.get_text(strip=True) if date_el else ''
    title = title_el.get_text(strip=True) if title_el else ''
    
    return {
        'id': news_id,
        'title': title,
        'url': url,
        'date': parse_date(date_text),
        'content': content,
    }


def parse_date(date_string: str) -> Optional[datetime]:
    """Parse Indonesian date format 'D MMMM YYYY'."""
    if not date_string:
        return None
    
    # Indonesian month names
    months = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    
    try:
        parts = date_string.lower().split()
        if len(parts) >= 3:
            day = int(parts[0])
            month = months.get(parts[1], 1)
            year = int(parts[2])
            return datetime(year, month, day)
    except (ValueError, IndexError):
        pass
    
    return None
