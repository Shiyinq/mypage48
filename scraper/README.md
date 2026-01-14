# JKT48 Scraper CLI Application

A robust, modular Python scraper for the JKT48 news, schedule and setlists.

## Features

-   **Robust Architecture**: Uses `curl_cffi` to mimic real browser TLS fingerprints, bypassing basic bot protections.
-   **Automated Cloudflare Bypass**: Integrates with **FlareSolverr** to automatically solve Cloudflare challenges (403 Forbidden) and refresh cookies.


## Prerequisites

-   Python 3.10+
-   [Docker](https://www.docker.com/) (Optional, required for auto-retry Cloudflare bypass)

## Installation

1.  Clone the repository.
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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

### 1. Basic Scraping

Fetch the latest data (Current News & Schedule):

```bash
# Fetch latest News
python jkt48scraper.py --news
# Output: data/news.current.json

# Fetch current & upcoming Schedule
python jkt48scraper.py --schedule
# Output: data/events.current.json

# Fetch Setlists
python jkt48scraper.py --setlist
# Output: data/setlists.json
```

### 2. Historical Schedule Scraping

Scrape schedule data for a specific year or a range of years.

```bash
# Scrape a specific year
python jkt48scraper.py --schedule 2012
# Output: data/schedule/events.schedule.2012.json

# Scrape a range of years
python jkt48scraper.py --schedule 2011-2015
# Outputs individual files for each year in data/schedule/
```

### 3. Merging Data

Merge scraped historical files into a single consolidated JSON file, enriched with member details.

```bash
# Option A: Scrape AND Merge immediately
python jkt48scraper.py --schedule 2011-2015 --merge
# Output: data/schedule/events.schedule_2011_to_2015.json

# Option B: Merge existing files in data/schedule/
python jkt48scraper.py --schedule-merge
```

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
├── jkt48scraper.py            # Main CLI entry point
├── requirements.txt           # Python dependencies
├── cookies.example.json       # Cookie template
├── .gitignore
├── data/                      # Output directory
│   ├── news.current.json
│   ├── events.current.json
│   └── schedule/              # Historical schedule data
├── src/
│   ├── __init__.py
│   ├── active.members.json    # Reference member data
│   ├── merger.py              # Logic for merging historical data
│   ├── agent/                 # Core networking & agent logic
│   │   ├── __init__.py
│   │   ├── browser.py         # Request handler with retry logic
│   │   ├── cookies.py         # Cookie management
│   │   └── flaresolverr.py    # FlareSolverr client
│   ├── news.py                # News scraper module
│   ├── schedule.py            # Schedule scraper module
│   ├── setlist.py             # Setlist scraper module
│   ├── theater.py             # Theater/Event detail scraper
│   └── utils.py               # General utilities
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
