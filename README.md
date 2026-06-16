# MyPage48

<div align="center">

![MyPage48](https://img.shields.io/badge/MyPage48-JKT48%20Theater%20Tracker-e41e2b?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDMgNXY2YzAgNS41NSAzLjg0IDEwLjc0IDkgMTIgNS4xNi0xLjI2IDktNi40NSA5LTEyVjVsLTktM3oiLz48L3N2Zz4=)

**A personal dashboard for JKT48 fans to track theater attendance, 2-shot collections, and spending statistics.**

[Features](#-features) · [Quick Start](#-quick-start) · [Deployment](#-deployment)

</div>

---

## ✨ Features

- 📊 **Dashboard Analytics** - View comprehensive statistics of your theater visits, spending, and attendance patterns
- 🤖 **AI-Powered Ticket Scanner** - Extract event details from ticket screenshots using Google Gemini
- 🎭 **Theater Tracking** - Log your theater show attendance with seat information and show details
- 📸 **2-Shot Collection** - Track your 2-shot photos with member statistics
- 🖼️ **Digital Photobook** - Browse your collected memories in a beautiful gallery view
- 🗺️ **Seat Map Visualization** - Interactive theater seat map showing your seating history
- 🏆 **Achievements System** - Unlock achievements based on your theater journey
- 👤 **Public Profile** - Share your theater stats with a public profile page (Wrapped)
- 📅 **Interactive Calendar** - Browse JKT48 schedule and events in a monthly view
- 📜 **Event History** - Comprehensive history of all past JKT48 events
- 📦 **Data Export** - Download your complete data including images in a ZIP archive
- 📺 **JKT48 Live Stream** - Watch Showroom and IDN Live with a real-time multiview experience
- 📉 **Oshi Sorter** - Rank your favorite JKT48 members with an interactive sorting tool
- 🌏 **Multi-language Support** - Available in English, Indonesian, and Japanese
- 🌙 **Dark Mode** - Beautiful dark-themed UI with glassmorphism design
- 🕷️ **Built-in Scraper** - Automated fetching of JKT48 schedule, news, and member data
- 💬 **Feedback System** - Built-in tool for reporting issues or suggestions
- 🛡️ **Admin Dashboard** - Comprehensive user management and content moderation tools

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Backend** | FastAPI |
| **Frontend** | Svelte & SvelteKit |
| **Database** | MongoDB |
| **Storage** | MinIO & Cloudflare R2 |
| **Reverse Proxy**| Nginx |
| **Analytics** | Umami |
| **LLM** | Google Gemini |
| **Styling** | Vanilla CSS & TailwindCSS |
| **Auth** | JWT Authentication |

## 📁 Project Structure

```
mypage48/
├── src/                   # Backend (FastAPI)
├── scraper/               # JKT48 Web Scraper
├── frontend/              # Frontend (SvelteKit)
├── nginx/                 # Nginx Configuration (Production)
├── scripts/               # Utility & Cron scripts
├── tests/                 # Backend tests
├── DEPLOYMENT.md          # PRODUCTION DEPLOYMENT GUIDE 🚀
├── docker-compose.yml     # Local Development Compose
├── docker-compose.prod.yml # Production Environment Compose
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 24+
- MongoDB 7+
- Docker & Docker Compose

### Local Development

The easiest way to get started is using the provided `Makefile`:

1. **Install Dependencies**
   ```bash
   make install
   ```

2. **Setup Environment Variables**
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

3. **Run All Services**
   ```bash
   make dev
   ```

   *Tip: Use `make help` to see all available management commands.*

   - **App:** http://localhost:5173
   - **API:** http://localhost:8000/docs
   - **MinIO:** http://localhost:9001

#### Alternative: Manual Setup

If you prefer not to use `make`, you can set up the project manually:

1. **Setup Backend**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements/base.txt -r requirements/dev.txt
   cp .env.example .env
   ```

2. **Setup Frontend**
   ```bash
   cd frontend && npm install && cp .env.example .env && cd ..
   ```

3. **Run All Services**
   ```bash
   sh scripts/start-all-dev.sh
   ```

## 🐳 Production Deployment

MyPage48 is now fully production-ready with a secure, automated infrastructure.

### Features
- **Nginx Reverse Proxy**: Subdomain routing for App, API, Analytics, and Storage.
- **Umami Analytics**: Privacy-focused, self-hosted visitor tracking.
- **Automated Scraper**: Periodic daily sync (12:00 AM) using isolated cron service.
- **Hardened Security**: Network isolation, Root DB authentication, and HTTPS ready.

### Guide
For a step-by-step production setup on a VPS, please follow the **[Deployment Guide](DEPLOYMENT.md)**.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ for JKT48 fans
</div>
