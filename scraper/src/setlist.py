"""Setlist scraper for JKT48 website."""
import time
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from .agent.browser import request


def extract_setlist_id_from_url(url: str) -> Optional[str]:
    """Extract setlist ID from URL like /theater/song-list/id/8"""
    match = re.search(r'/theater/song-list/id/(\d+)', url)
    return match.group(1) if match else None


def extract_song_id_from_url(url: str) -> Optional[str]:
    """Extract song ID from URL like /theater/song/id/76"""
    match = re.search(r'/theater/song/id/(\d+)', url)
    return match.group(1) if match else None


def get_all_setlists(headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    Get all setlists from https://jkt48.com/theater?lang=id
    Scrapes the "Lagu Panggung" section.
    """
    url = 'https://jkt48.com/theater?lang=id'
    
    response = request('GET', url, headers=headers or {}, impersonate='chrome')
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    setlist_section = None
    for section in soup.select('.entry-nav'):
        title = section.select_one('.entry-nav__title')
        if title and 'Lagu Panggung' in title.get_text():
            setlist_section = section
            break
    
    if not setlist_section:
        return []
    
    setlists = []
    items = setlist_section.select('.entry-nav__inner--item')
    
    for item in items:
        link = item.select_one('h3 a')
        if link:
            href = link.get('href', '')
            title = link.get_text(strip=True)
            setlist_id = extract_setlist_id_from_url(href)
            
            setlists.append({
                'id': setlist_id,
                'setlistId': title.replace(' ', '').lower().strip(),
                'title': title,
                'url': href,
            })
    
    return setlists


def get_setlist_songs(
    setlist_id: str,
    headers: Optional[Dict[str, str]] = None,
    retry: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all songs from a specific setlist.
    Example URL: https://jkt48.com/theater/song-list/id/8?lang=id
    """
    try:
        url = f'https://jkt48.com/theater/song-list/id/{setlist_id}?lang=id'
        
        response = request('GET', url, headers=headers or {}, impersonate='chrome')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        songs = []
        song_items = soup.select('.entry-news .entry-news__list .entry-news__list--item')
        
        for item in song_items:
            link = item.select_one('h3 a')
            if link:
                href = link.get('href', '')
                song_title = link.get_text(strip=True)
                song_id = extract_song_id_from_url(href)
                
                songs.append({
                    'id': song_id,
                    'title': song_title,
                })
        
        return songs
    
    except Exception as e:
        if retry > 5:
            raise e
        time.sleep(0.5)
        return get_setlist_songs(setlist_id, headers, retry + 1)


def get_song_lyrics(
    song_id: str,
    headers: Optional[Dict[str, str]] = None,
    retry: int = 0
) -> Dict[str, Any]:
    """
    Get song lyrics from a specific song page.
    Example URL: https://jkt48.com/theater/song/id/76?lang=id
    """
    try:
        url = f'https://jkt48.com/theater/song/id/{song_id}?lang=id'
        
        response = request('GET', url, headers=headers or {}, impersonate='chrome')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get song title from h3 inside entry-news__detail
        title_el = soup.select_one('.entry-news__detail h3')
        title = title_el.get_text(strip=True) if title_el else ''
        
        lyrics_el = soup.select_one('.entry-news__detail > div')
        if lyrics_el:
            inner_html = lyrics_el.decode_contents()
            # Replace <br>, <br/>, <br /> with newlines
            lyrics = re.sub(r'<br\s*/?>', '\n', inner_html)
            # Remove any other HTML tags
            lyrics = re.sub(r'<[^>]+>', '', lyrics)
            # Clean up extra whitespace but preserve line breaks
            lyrics = '\n'.join(line.strip() for line in lyrics.split('\n'))
        else:
            lyrics = ''
        
        return {
            'id': song_id,
            'title': title,
            'lyric': lyrics.strip(),
        }
    
    except Exception as e:
        if retry > 5:
            raise e
        time.sleep(0.5)
        return get_song_lyrics(song_id, headers, retry + 1)


def get_setlist_with_songs_and_lyrics(
    setlist_id: str,
    setlist_title: str,
    setlist_url: str,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Get a setlist with all its songs and lyrics.
    """
    songs = get_setlist_songs(setlist_id, headers)
    
    song_titles = []
    songDetails = []
    
    for song in songs:
        song_titles.append(song['title'])
        
        print(f"  - Fetching lyrics: {song['title']}")
        time.sleep(0.35)  # Rate limiting
        
        lyric_data = get_song_lyrics(song['id'], headers)
        songDetails.append({
            'id': song['id'],
            'title': lyric_data['title'],
            'lyric': lyric_data['lyric'],
        })
    
    return {
        'id': setlist_id,
        'setlistId': setlist_title.replace(' ', '').lower().strip(),
        'title': setlist_title,
        'songs': song_titles,
        'songDetails': songDetails,
    }


def fetch_all_setlists_with_songs_and_lyrics(
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all setlists with their songs and lyrics.
    """
    setlists = get_all_setlists(headers)
    results = []
    
    for i, setlist in enumerate(setlists):
        print(f"[{i+1}/{len(setlists)}] Fetching setlist: {setlist['title']}")
        time.sleep(0.35)  # Rate limiting
        
        setlist_data = get_setlist_with_songs_and_lyrics(
            setlist['id'],
            setlist['title'],
            setlist['url'],
            headers
        )
        results.append(setlist_data)
    
    return results
