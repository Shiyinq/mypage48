# JKT48 Scraper CLI Application

A robust, modular Python scraper for JKT48 news, members, and schedule data.

## Features

-   **News Scraper**: Fetch news with pagination support (single page, range, or all).
-   **Members Scraper**: Fetch and format member profiles from the JKT48 API.
-   **Schedule Scraper**: Fetch current/upcoming events or historical schedules by year.
-   **MongoDB Sync**: Sync fetched data directly to MongoDB with `--sync`.
-   **Robust Architecture**: Uses `curl_cffi` to mimic real browser TLS fingerprints.
-   **Automated Cloudflare Bypass**: Integrates with **FlareSolverr** to solve Cloudflare challenges.

## Prerequisites

-   Python 3.10+
-   MongoDB (required for `--sync`)
-   [Docker](https://www.docker.com/) (Optional, for FlareSolverr Cloudflare bypass)

## Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Setup configuration:
    ```bash
    cp cookies.example.json cookies.json
    ```

## Usage

The main entry point is `jkt48scraper.py`.

### News

```bash
# Fetch latest news (default: page 1)
python jkt48scraper.py --news

# Fetch specific page
python jkt48scraper.py --news 5

# Fetch range of pages
python jkt48scraper.py --news 1-10

# Fetch all available pages
python jkt48scraper.py --news all
```

### Members

```bash
python jkt48scraper.py --members
```

### Schedule

```bash
# Fetch current & upcoming events
python jkt48scraper.py --schedule

# Fetch a specific year
python jkt48scraper.py --schedule 2012

# Fetch a range of years
python jkt48scraper.py --schedule 2011-2023

# Fetch all years (2011 to present)
python jkt48scraper.py --schedule all
```

### Merging Historical Data

Merge scraped historical schedule files into a single consolidated JSON.

```bash
# Scrape AND merge
python jkt48scraper.py --schedule 2011-2023 --merge

# Merge existing files only
python jkt48scraper.py --schedule-merge
```

### Sync to MongoDB

Add `--sync` to any command to upsert fetched data into MongoDB.

```bash
python jkt48scraper.py --news --sync
python jkt48scraper.py --members --sync
python jkt48scraper.py --schedule --sync
```

Data is upserted (insert or update) based on unique IDs, so running `--sync` multiple times will never create duplicates.

## Cloudflare Bypass (FlareSolverr)

To enable the "Lazy Retry" mechanism (automatically solvng 403 errors), you must run a FlareSolverr instance:

```bash
docker run -d \
  --name=flaresolverr \
  -p 8191:8191 \
  -e LOG_LEVEL=info \
  ghcr.io/flaresolverr/flaresolverr:latest
```

The scraper's `src/agent/browser.py` will automatically detect 403 errors, contact `localhost:8191` to get new cookies, and retry the request.

## Project Structure

```
.
├── jkt48scraper.py            # Main CLI entry point (Template Method pattern)
├── requirements.txt           # Python dependencies
├── cookies.example.json       # Cookie template
├── data/                      # Output directory
│   ├── news.current.json
│   ├── members.current.json
│   ├── events.current.json
│   └── schedule/              # Historical schedule data
├── src/
│   ├── __init__.py
│   ├── active.members.json    # Reference member data
│   ├── db.py                  # MongoDB connection & upsert utility
│   ├── merger.py              # Logic for merging historical data
│   ├── members.py             # Members scraper module
│   ├── news.py                # News scraper module
│   ├── schedule.py            # Schedule & theater scraper module
│   ├── utils.py               # General utilities
│   └── agent/                 # Core networking & agent logic
│       ├── __init__.py
│       ├── browser.py         # Request handler with retry logic
│       ├── cookies.py         # Cookie management
│       └── flaresolverr.py    # FlareSolverr client
└── README.md
```

## Legal Disclaimer

This tool is created for **educational, research, and personal non-commercial fan projects**.

1.  **Public Data**: This scraper only accesses data that is publicly available on the JKT48 website. It does not attempt to bypass authentication for private data or exploit security vulnerabilities.
2.  **Server Load**: The script includes rate limiting (`time.sleep`) to avoid overwhelming the target server. Users are responsible for maintaining reasonable request rates.
3.  **Terms of Service & Robots.txt**: Users should verify the Terms of Service (ToS) of the target website. 
    > **Note**: As of the creation of this project, `https://jkt48.com/robots.txt` contains:
    > ```
    > User-agent: *
    > Sitemap: http://jkt48.com/sitemap/xml
    > ```
    > This implies that the site **allows** automated access (`Disallow` is empty). However, standard web etiquette (politeness, rate limiting) must still be followed to respect server resources. The developers are not responsible for any misuse.
4.  **Copyright**: All data scraped belongs to its respective owners (JKT48 Operation Team). Do not use the data for commercial purposes without permission.

## License

[MIT](../LICENSE)

**Clarification**: The MIT License applies to the **source code** of this tool. The **data** scraped using this tool belongs to JKT48 and is subject to their terms. Users strictly responsible for how they use the data.
