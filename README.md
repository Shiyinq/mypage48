# MyPage48

<div align="center">

![MyPage48](https://img.shields.io/badge/MyPage48-JKT48%20Theater%20Tracker-e41e2b?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDMgNXY2YzAgNS41NSAzLjg0IDEwLjc0IDkgMTIgNS4xNi0xLjI2IDktNi40NSA5LTEyVjVsLTktM3oiLz48L3N2Zz4=)

**A personal dashboard for JKT48 fans to track theater attendance, 2-shot collections, and spending statistics.**

[Features](#features) · [Quick Start](#quick-start) · [Deployment](#deployment)

</div>

---

## ✨ Features

- 📊 **Dashboard Analytics** - View comprehensive statistics of your theater visits, spending, and attendance patterns
- 🎭 **Theater Tracking** - Log your theater show attendance with seat information and show details
- 📸 **2-Shot Collection** - Track your 2-shot photos with member statistics
- 🗺️ **Seat Map Visualization** - Interactive theater seat map showing your seating history
- 📅 **Monthly & Daily Stats** - Analyze your attendance patterns by month and day of week
- 🏆 **Achievements System** - Unlock achievements based on your theater journey
- 👤 **Public Profile** - Share your theater stats with a public profile page (Wrapped)
- 🌏 **Multi-language Support** - Available in English, Indonesian, and Japanese
- 🌙 **Dark Mode** - Beautiful dark-themed UI with glassmorphism design

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.10+) |
| **Frontend** | SvelteKit 2.x |
| **Database** | MongoDB |
| **Styling** | TailwindCSS |
| **Auth** | JWT Authentication |

## 📁 Project Structure

```
mypage48/
├── src/                    # Backend (FastAPI)
│   ├── achievements/       # Achievement system
│   ├── auth/              # Authentication & OAuth
│   ├── dashboard/         # Dashboard statistics API
│   ├── members/           # JKT48 members data
│   ├── setlists/          # Setlist information
│   ├── tickets/           # Theater ticket logging
│   ├── users/             # User management
│   └── ...
├── frontend/              # Frontend (SvelteKit)
│   ├── src/
│   │   ├── lib/          # Components, stores, utilities
│   │   └── routes/       # Application pages
│   └── ...
├── scripts/               # Utility scripts
├── tests/                 # Backend tests
└── docker-compose.yml     # Docker deployment
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)

### Backend Setup

1. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements/dev.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB URI and other settings
   ```

4. **Run development server**
   ```bash
   sh scripts/start-dev.sh
   ```
   
   API docs available at: http://localhost:8000/docs

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with API URL and other settings
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```
   
   App available at: http://localhost:5173

### Run Both Services

Use the convenience script to start both backend and frontend:

```bash
sh scripts/start-all-dev.sh
```

## 🧹 Code Quality

**Backend:**
```bash
sh scripts/lint-format.sh
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run format
npm run check
```

## 🐳 Deployment

### Docker Compose (Recommended)

1. **Configure environment files**
   ```bash
   cp .env.example .env
   cd frontend && cp .env.example .env && cd ..
   ```

2. **Build and run containers**
   ```bash
   docker compose up --build -d
   ```

3. **Access the application**
   - Frontend: http://localhost:5050
   - Backend: http://localhost:8000

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
Made with ❤️ for JKT48 fans
</div>
