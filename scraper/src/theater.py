"""Theater scraper for JKT48 website."""
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .utils import extract_id_from_url, extract_team_id, get_theater_id
from .agent.browser import request


def parse_theater_date(date_string: str) -> Optional[datetime]:
    """Parse theater date string like 'senin, 1.2.2024 10:00'."""
    try:
        # Split by 'show' to separate date and time
        parts = date_string.lower().split('show')
        date_part = parts[0].strip()
        time_part = parts[1].strip() if len(parts) > 1 else None
        
        # Remove day name if present (e.g., "senin, ")
        if ',' in date_part:
            date_part = date_part.split(',')[1].strip()
        
        # Parse date (format: D.M.YYYY)
        date_match = re.match(r'(\d{1,2})[.:](\d{1,2})[.:](\d{4})', date_part)
        if not date_match:
            return None
        
        day, month, year = map(int, date_match.groups())
        
        hour, minute = 0, 0
        if time_part:
            time_match = re.match(r'(\d{1,2})[.:](\d{2})', time_part)
            if time_match:
                hour, minute = map(int, time_match.groups())
        
        return datetime(year, month, day, hour, minute)
    
    except (ValueError, IndexError):
        return None


def get_theater_detail(
    theater_id: str,
    retry: int = 1,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Get theater schedule detail."""
    try:
        relative_url = f'/theater/schedule/id/{theater_id}?lang=id'
        url = f'https://jkt48.com{relative_url}'
        
        response = request('GET', url, headers=headers or {}, impersonate='chrome')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the schedule table
        table = soup.select_one(
            'body > div.container > div.row > div > div > div:nth-child(5) > '
            'div.table-responsive.table-pink__scroll > table'
        )
        
        if not table:
            raise Exception('Show table not found!')
        
        shows = table.select('tbody tr')
        if not shows:
            raise Exception('Show not found!')
        
        theater_data: List[Dict[str, Any]] = []
        member_map: Dict[str, Dict[str, Any]] = {}
        url_theater_id = get_theater_id(url) or url
        
        for num, show in enumerate(shows):
            # Get title and team
            title_td = show.select_one('td:nth-child(2)')
            title = title_td.get_text(strip=True) if title_td else ''
            
            team_img = show.select_one('td:nth-child(2) img')
            team_src = team_img.get('src', '') if team_img else ''
            
            # Get date
            date_td = show.select_one('td:nth-child(1)')
            date_string = date_td.get_text(strip=True).lower() if date_td else ''
            date = parse_theater_date(date_string)
            
            if date is None:
                # raise Exception(f'Date kosong, {url}')
                # Log instead of crash if date parsing fails?
                # But it's critical for schedule
                 raise Exception(f'Date kosong, {url}')
            
            # Get members
            members: Dict[str, Dict[str, Any]] = {}
            seitansai: List[Dict[str, Any]] = []
            member_links = show.select('td:nth-child(3) a')
            
            for member_link in member_links:
                member_id = extract_id_from_url(member_link.get('href', '0'))
                member_name = member_link.get_text(strip=True)
                member_url = member_link.get('href', '')
                
                if member_id in members:
                    # Duplicate means seitansai (birthday)
                    seitansai.append({**members[member_id]})
                else:
                    members[member_id] = {
                        'id': member_id,
                        'name': member_name,
                        'url': member_url,
                    }
                
                member_map[member_id] = {
                    'id': member_id,
                    'name': member_name,
                    'url': member_url,
                }
            
            setlist_id = title.replace(' ', '').lower().strip()
            show_id = f'{url_theater_id}-{num}' if len(shows) > 1 else url_theater_id

            memberIds = list(members.keys())
            seitansaiIds = [s['id'] for s in seitansai]
            
            theater_data.append({
                'id': show_id,
                'setlistId': setlist_id,
                'title': title,
                'team': {
                    'id': extract_team_id(team_src) or '',
                    'img': team_src,
                },
                'graduationIds': [],
                'date': date,
                'memberIds': memberIds,
                'seitansaiIds': seitansaiIds if len(memberIds) > 1 else memberIds, # if only one member, it's birthday.
                'url': relative_url,
            })
        
        return {
            'show': theater_data,
            'members': list(member_map.values()),
        }
    
    except Exception as e:
        if retry > 20:
            raise e
        print(f'Error fetching {theater_id}')
        print(f'Retry {theater_id}')
        time.sleep(1)
        return get_theater_detail(theater_id, retry + 1, headers)
