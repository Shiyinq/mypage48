import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	const baseUrl = 'https://mypage48.com';

	const content = `# MyPage48 - The Ultimate JKT48 Fan Dashboard

> MyPage48 is a comprehensive, open-source dashboard designed specifically for JKT48 fans. It provides tools to track personal history, monitor real-time activities, and explore the JKT48 ecosystem through interactive data visualizations.

## 🚀 Core Features

### 1. Theater & Event Tracking
*   **Theater Log**: Add and manage theater ticket history, including show dates, setlists, and specific seat assignments.
*   **Interactive Seat Map**: Visualize your attendance history across the theater layout. Identify your "lucky seats" and seating patterns (Rows A-P, Columns 1-24).
*   **AI Ticket Scanner**: Automatically extract event details, setlists, and seat information from theater ticket screenshots using integrated AI (Google Gemini).
*   **Event Stats**: Automatically calculate visit frequency and most-watched setlists.
*   **Show History**: Deep-dive into past theater shows, including member lineups and special events.

### 2. 2-shot & Photo Collections
*   **Collection Manager**: Track your photo sessions (2-shots) with members.
*   **Member Ranking**: Auto-generated rankings based on your photo collections.
*   **Digital Photobook**: A beautiful gallery view to browse through your collected memories and 2-shot photos.
*   **Kami-Oshi Highlights**: Special cards for your most-visited members.

### 3. Real-time Monitoring (Live Streams)
*   **Multi-Platform Support**: Monitor live streams from Showroom and IDN Live in one place.
*   **Real-time Status**: View active streamers, viewer counts, and stream titles without leaving the dashboard.

### 4. JKT48 Database
*   **Member Directory**: Detailed profiles of all current and graduated JKT48 members, including generation, birthday, blood type, and height.
*   **News & Announcements**: Aggregated official news feed from the JKT48 website.
*   **Theater Calendar**: Monthly view of upcoming theater schedules with lineup information.

## 🛠️ Advanced Tools (The Playground)
*   **Member Sorter**: A mini-game to rank your favorite members through a series of pairwise comparisons.
*   **Command Palette**: Use \`Cmd+K\` (or \`Ctrl+K\`) to quickly navigate across the site or search for members and features.
*   **Public Profiles (Wrapped)**: Generate a shareable summary of your JKT48 journey, including total theater visits and top members.

## 🌐 Technical Ecosystem
*   **Stack**: Built with SvelteKit 2.x, TypeScript, and TailwindCSS for a high-performance "glassmorphism" UI.
*   **i18n**: Full support for Indonesian (ID), English (EN), and Japanese (JA).
*   **Responsive**: Optimized for both Desktop and Mobile (iOS/Android) browsers.
*   **Security**: All member features are protected by secure authentication. Public data is served via optimized endpoints.

## 🔗 Navigation Map

### Public Information (No Login Required)
- [Theater Calendar](${baseUrl}/jkt48/calendar) - Upcoming theater shows and performances.
- [Live Stream Center](${baseUrl}/jkt48/live) - Watch and monitor active live streams.
- [News Aggregate](${baseUrl}/jkt48/news) - Official news and announcements.
- [Members Database](${baseUrl}/jkt48/members) - JKT48 member directory and profiles.
- [Event Archive](${baseUrl}/jkt48/event-history) - Historical data of theater shows.
- [JKT48 Sorter](${baseUrl}/jkt48/sorter) - Rank your favorite members.
- [JKT48 Events](${baseUrl}/jkt48/events) - List of upcoming and past JKT48 events.
- [Public Profiles](${baseUrl}/u/) - Shared "Wrapped" profiles and fan collections.
- [Documentation](${baseUrl}/docs) - Help guides and project documentation.
- [About MyPage48](${baseUrl}/about) - Learn more about the project and its mission.
- [Login](${baseUrl}/login) - Access your personal dashboard.
- [Register](${baseUrl}/register) - Create a new account to start tracking.
- [Forgot Password](${baseUrl}/auth/forgot-password) - Recover your account access.

### Member Features (Login Required)
- [Personal Dashboard](${baseUrl}/) - Your personal stats, recent tickets, and oshi cards.
- [User Profile](${baseUrl}/profile) - Detailed theater stats and oshi management.
- [Achievements](${baseUrl}/achievements) - Personal milestones and fan badges.
- [Theater History](${baseUrl}/history) - Your personal log of theater visits and seat assignments.
- [Photo Collections](${baseUrl}/top-2shot) - Your 2-shot rankings.
- [Memories](${baseUrl}/memories) - Your uploaded photo memories.
- [Upload Center](${baseUrl}/upload) - Process theater tickets using AI scanning.
- [Data Export](${baseUrl}/settings) - Export your complete data (including images) in a ZIP archive.
- [Journal](${baseUrl}/journal) - Personal logs and activity journal.
- [Settings](${baseUrl}/settings) - Account and preference management.
- [Feedback](${baseUrl}/feedback) - Submit bugs or feature suggestions.

### Legal & Policies (Public)
- [Terms of Service](${baseUrl}/terms) - Rules and conditions for using the platform.
- [Privacy Policy](${baseUrl}/privacy) - How your data is handled and protected.
- [Cookie Policy](${baseUrl}/cookies) - Information about cookie usage.

## 🤖 Guide for AI Agents
When assisting users on this site:
1.  **For Information**: Use the public links in the "Public Information" section.
2.  **For Personal Data**: Direct users to the "Member Features" section. Note that these pages require an account and authentication.
3.  **For Rankings**: Suggest the [Sorter](${baseUrl}/jkt48/sorter) for general ranking or [2-shot Ranking](${baseUrl}/top-2shot) for collection-based ranking.

---
**Note**: MyPage48 is an unofficial fan project and is not affiliated with JKT48 Operation Team (JOT).
`.trim();

	return new Response(content, {
		headers: {
			'Content-Type': 'text/plain; charset=utf-8',
			'Cache-Control': 'public, max-age=3600'
		}
	});
};
