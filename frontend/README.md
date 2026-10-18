# MyPage48 Frontend

The frontend application for **MyPage48** - a personal dashboard for JKT48 fans to track theater attendance and 2-shot collections.

## 🛠️ Tech Stack

- **Framework**: Svelte 5 & SvelteKit 2
- **Styling**: TailwindCSS v4 with custom glassmorphism design
- **Icons**: Lucide Svelte
- **State Management**: Svelte 5 runes & stores
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
│   │   ├── stores/       # Svelte stores
│   │   ├── types/        # TypeScript definitions
│   │   └── utils/        # Utility functions
│   └── routes/
│       ├── (public)/     # Public marketing, legal, and docs pages
│       ├── auth/         # OAuth callback routes
│       ├── page48/       # Social feed, trending, notifications
│       ├── live/         # Showroom & IDN Live multiview
│       ├── sorter/       # Oshi sorter
│       ├── history/      # Ticket history page
│       ├── memories/     # Photo memories
│       ├── profile/      # User profile & settings
│       ├── theater/      # Theater, shows, setlists
│       ├── top-2shot/    # 2-shot ranking
│       ├── u/            # Public profile pages
│       └── upload/       # Ticket upload
├── static/               # Static assets
└── svelte.config.js      # SvelteKit configuration
```

## 🚀 Development

### Prerequisites

- Node.js 24+
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

| Command           | Description               |
| ----------------- | ------------------------- |
| `npm run dev`     | Start development server  |
| `npm run build`   | Build for production      |
| `npm run preview` | Preview production build  |
| `npm run check`   | Type-check the codebase   |
| `npm run lint`    | Run ESLint                |
| `npm run format`  | Format code with Prettier |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

<div align="center">
Made with ❤️ for JKT48 fans
</div>
