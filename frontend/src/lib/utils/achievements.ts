import type { Ticket } from '$lib/types';
import type { ComponentType } from 'svelte';
import {
    Trophy,
    Star,
    Calendar,
    Crown,
    Zap,
    Heart,
    Wallet,
    Armchair,
    Award,
    Medal,
    Binoculars,
    Sparkles,
    History,
    Flame,
    Ticket as TicketIcon
} from 'lucide-svelte';

export interface Milestone {
    id: string;
    title: string;
    description: string;
    icon: ComponentType;
    isUnlocked: boolean;
    progress?: string;
    color: string;
}

export function calculateMilestones(tickets: Ticket[]): Milestone[] {
    const totalShows = tickets.length;

    // Date Calculations
    const sortedDates = [...tickets]
        .map((t) => new Date(t.event.date).getTime())
        .sort((a, b) => a - b);

    const firstDate = sortedDates[0];
    const lastDate = sortedDates[sortedDates.length - 1];
    const timeSpanDays =
        firstDate && lastDate ? (lastDate - firstDate) / (1000 * 60 * 60 * 24) : 0;

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

    // Full Row Collection (A-J)
    const collectedRows = new Set(
        tickets.map((t) => t.seat.section.trim().toUpperCase().charAt(0))
    );
    const targetRows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
    const uniqueRowsCount = targetRows.filter((r) => collectedRows.has(r)).length;

    // Spending
    const totalSpent = tickets.reduce((acc, t) => acc + t.price, 0);

    return [
        {
            id: 'first_show',
            title: 'First Step',
            description: 'Attended your first theater show',
            icon: Heart,
            isUnlocked: totalShows >= 1,
            color: 'red'
        },
        {
            id: 'regular_visitor',
            title: 'Regular Visitor',
            description: 'Attended 10 shows',
            icon: TicketIcon,
            isUnlocked: totalShows >= 10,
            progress: `${Math.min(totalShows, 10)}/10`,
            color: 'orange'
        },
        {
            id: 'dedicated_fan_50',
            title: 'Dedicated Fan',
            description: 'Attended 50 shows',
            icon: Award,
            isUnlocked: totalShows >= 50,
            progress: `${Math.min(totalShows, 50)}/50`,
            color: 'cyan'
        },
        {
            id: 'century_club_100',
            title: 'Century Club',
            description: 'Attended 100 shows',
            icon: Medal,
            isUnlocked: totalShows >= 100,
            progress: `${Math.min(totalShows, 100)}/100`,
            color: 'violet'
        },
        {
            id: 'theater_icon_150',
            title: 'Theater Icon',
            description: 'Attended 150 shows',
            icon: Zap,
            isUnlocked: totalShows >= 150,
            progress: `${Math.min(totalShows, 150)}/150`,
            color: 'fuchsia'
        },
        {
            id: 'legendary_wota_200',
            title: 'Legendary Wota',
            description: 'Attended 200 shows',
            icon: Crown,
            isUnlocked: totalShows >= 200,
            progress: `${Math.min(totalShows, 200)}/200`,
            color: 'rose'
        },
        {
            id: 'theater_kami_300',
            title: 'Theater Kami',
            description: 'Attended 300 shows',
            icon: Sparkles,
            isUnlocked: totalShows >= 300,
            progress: `${Math.min(totalShows, 300)}/300`,
            color: 'purple'
        },
        {
            id: 'absolute_legend_500',
            title: 'Absolute Legend',
            description: 'Attended 500 shows',
            icon: Trophy,
            isUnlocked: totalShows >= 500,
            progress: `${Math.min(totalShows, 500)}/500`,
            color: 'amber'
        },
        // Same Show Milestones
        {
            id: 'super_fan',
            title: 'Super Fan',
            description: 'Watched the same event 10 times',
            icon: Star,
            isUnlocked: maxSameShow >= 10,
            progress: `${Math.min(maxSameShow, 10)}/10`,
            color: 'yellow'
        },
        {
            id: 'mega_fan',
            title: 'Mega Fan',
            description: 'Watched the same event 20 times',
            icon: Sparkles,
            isUnlocked: maxSameShow >= 20,
            progress: `${Math.min(maxSameShow, 20)}/20`,
            color: 'orange'
        },
        {
            id: 'ultra_fan',
            title: 'Ultra Fan',
            description: 'Watched the same event 30 times',
            icon: Flame,
            isUnlocked: maxSameShow >= 30,
            progress: `${Math.min(maxSameShow, 30)}/30`,
            color: 'red'
        },
        // Anniversary Milestones
        {
            id: 'theater_enthusiast',
            title: 'Theater Enthusiast',
            description: '1 year anniversary since first show',
            icon: Calendar,
            isUnlocked: timeSpanDays >= 365,
            progress: `${Math.floor(timeSpanDays)}/365 days`,
            color: 'blue'
        },
        {
            id: 'theater_veteran',
            title: 'Theater Veteran',
            description: '2 year anniversary since first show',
            icon: History,
            isUnlocked: timeSpanDays >= 730,
            progress: `${Math.floor(timeSpanDays)}/730 days`,
            color: 'indigo'
        },
        {
            id: 'theater_legend',
            title: 'Theater Legend',
            description: '3 year anniversary since first show',
            icon: Crown,
            isUnlocked: timeSpanDays >= 1095,
            progress: `${Math.floor(timeSpanDays)}/1095 days`,
            color: 'violet'
        },
        // Row Milestones
        {
            id: 'elite_row',
            title: 'Elite Seat',
            description: 'Sat in the legendary Row A',
            icon: Crown,
            isUnlocked: hasRowA,
            color: 'purple'
        },
        {
            id: 'back_row_warrior',
            title: 'Back Row Warrior',
            description: 'Watched from the furthest row (Row J)',
            icon: Binoculars,
            isUnlocked: hasRowJ,
            color: 'indigo'
        },
        {
            id: 'seat_explorer',
            title: 'Seat Explorer',
            description: 'Collected a ticket for every row (A-J)',
            icon: Armchair,
            isUnlocked: uniqueRowsCount >= 10,
            progress: `${uniqueRowsCount}/10`,
            color: 'pink'
        },
        // Spending Milestone
        {
            id: 'supporter',
            title: 'Top Supporter',
            description: 'Spent over 5 Million IDR on tickets',
            icon: Wallet,
            isUnlocked: totalSpent >= 5000000,
            progress: `${(Math.min(totalSpent, 5000000) / 1000000).toFixed(1)}/5M`,
            color: 'emerald'
        }
    ] as Milestone[];
}

export function calculateTotalAchievements(tickets: Ticket[]): number {
    return calculateMilestones(tickets).filter((m) => m.isUnlocked).length;
}
