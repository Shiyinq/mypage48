# MyPage48 Frontend

The frontend application for **MyPage48** - a personal dashboard for JKT48 fans to track theater attendance and 2-shot collections.

## 🛠️ Tech Stack

- **Framework**: SvelteKit 2.x
- **Styling**: TailwindCSS with custom glassmorphism design
- **Icons**: Lucide Svelte
- **State Management**: Svelte Stores
- **i18n**: Custom implementation (EN, ID, JA)
- **API Client**: Custom fetch wrapper with JWT auth

## 📁 Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── apis/         # API client functions
│   │   ├── components/   # Reusable UI components
│   │   ├── i18n/         # Internationalization
│   │   ├── services/     # External services (Gemini AI)
│   │   ├── stores/       # Svelte stores
│   │   ├── types/        # TypeScript definitions
│   │   └── utils/        # Utility functions
│   └── routes/
│       ├── (app)/        # Main app layout group
│       ├── auth/         # OAuth callback routes
│       ├── history/      # Ticket history page
│       ├── memories/     # Photo memories
│       ├── profile/      # User profile & settings
│       ├── theater/      # Theater, shows, setlists
│       ├── top-2shot/    # 2-shot ranking
│       ├── u/            # Public profile pages
│       └── upload/       # Ticket upload
├── static/               # Static assets
└── tests/                # E2E tests
```

## 🚀 Development

### Prerequisites

- Node.js 18+
- Backend API running (see main README)

### Setup

```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start dev server
npm run dev

# Or open in browser automatically
npm run dev -- --open
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run check` | Type-check the codebase |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |

## 🎨 Key Components

- **Dashboard**: Stats overview with charts and seat map
- **TheaterSeatMap**: Interactive visualization of seating history
- **TicketCard**: Display theater ticket information
- **MemberSelector**: Search and select JKT48 members
- **OshiSelectionModal**: Set favorite member (oshi)

## 🌐 Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard with statistics |
| `/theater` | Theater schedule & show info |
| `/history` | Ticket history |
| `/top-2shot` | 2-shot collection ranking |
| `/memories` | Photo memories gallery |
| `/profile` | User profile |
| `/settings` | User settings |
| `/u/[username]` | Public profile (Wrapped) |
| `/upload` | Upload theater tickets |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

<div align="center">
Made with ❤️ for JKT48 fans
</div>
