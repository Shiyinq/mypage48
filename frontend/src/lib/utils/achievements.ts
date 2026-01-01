import type { Ticket } from '$lib/types';

export function calculateTotalAchievements(tickets: Ticket[]): number {
    if (tickets.length === 0) return 0;

    let count = 0;
    const totalShows = tickets.length;

    // Date Calculations
    const sortedDates = [...tickets]
        .map((t) => new Date(t.event.date).getTime())
        .sort((a, b) => a - b);
    const firstDate = sortedDates[0];
    const lastDate = sortedDates[sortedDates.length - 1];
    const timeSpanDays = firstDate && lastDate ? (lastDate - firstDate) / (1000 * 60 * 60 * 24) : 0;

    // Show Counts
    const showCounts: Record<string, number> = {};
    tickets.forEach((t) => {
        const title = t.event.title.trim();
        showCounts[title] = (showCounts[title] || 0) + 1;
    });
    const maxSameShow = Math.max(...Object.values(showCounts), 0);

    // Row Calculations
    const hasRowA = tickets.some((t) => t.seat.section.toUpperCase() === 'A');
    const hasRowJ = tickets.some((t) => t.seat.section.toUpperCase() === 'J');
    const collectedRows = new Set(
        tickets.map((t) => t.seat.section.trim().toUpperCase().charAt(0))
    );
    const targetRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
    const uniqueRowsCount = targetRows.filter((r) => collectedRows.has(r)).length;

    // Spending
    const totalSpent = tickets.reduce((acc, t) => acc + t.price, 0);

    // Count unlocked milestones
    if (totalShows >= 1) count++; // First Step
    if (totalShows >= 10) count++; // Regular Visitor
    if (totalShows >= 50) count++; // Dedicated Fan
    if (totalShows >= 100) count++; // Century Club
    if (totalShows >= 150) count++; // Theater Icon
    if (totalShows >= 200) count++; // Legendary Wota
    if (maxSameShow >= 10) count++; // Super Fan
    if (maxSameShow >= 20) count++; // Mega Fan
    if (maxSameShow >= 30) count++; // Ultra Fan
    if (timeSpanDays >= 365) count++; // Theater Enthusiast
    if (timeSpanDays >= 730) count++; // Theater Veteran
    if (timeSpanDays >= 1095) count++; // Theater Legend
    if (hasRowA) count++; // Elite Seat
    if (hasRowJ) count++; // Back Row Warrior
    if (uniqueRowsCount >= 10) count++; // Seat Explorer
    if (totalSpent >= 5000000) count++; // Top Supporter

    return count;
}
