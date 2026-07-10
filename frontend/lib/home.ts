import type { MatchSummary, StandingsResponse } from '@/lib/api';

// How many played fixtures the Home screen surfaces as "recent results".
export const RECENT_RESULTS_LIMIT = 5;

export interface HomeSummary {
  // The soonest unplayed fixture, or null once the season is over.
  nextMatch: MatchSummary | null;
  // Most recent played fixtures first, capped at RECENT_RESULTS_LIMIT.
  recentResults: MatchSummary[];
  // 1-based league position of the signed-in team, or null when unplaced.
  position: number | null;
  totalTeams: number;
  divisionLevel: number | null;
  seasonNumber: number | null;
}

// Derives the Home dashboard from the fixtures list and the league table, so
// the page itself stays free of business logic. `matches` is assumed ordered by
// round ascending (as the API returns it); results are re-sorted most-recent
// first for display.
export function deriveHomeSummary(
  matches: MatchSummary[],
  standings: StandingsResponse,
): HomeSummary {
  const nextMatch = matches.find((match) => !match.played) ?? null;
  const recentResults = matches
    .filter((match) => match.played)
    .sort((a, b) => b.round - a.round)
    .slice(0, RECENT_RESULTS_LIMIT);

  const index = standings.entries.findIndex((entry) => entry.isCurrentUserTeam);

  return {
    nextMatch,
    recentResults,
    position: index >= 0 ? index + 1 : null,
    totalTeams: standings.entries.length,
    divisionLevel: standings.divisionLevel,
    seasonNumber: standings.seasonNumber,
  };
}

// The signed-in team's result in a played fixture, from its own perspective.
export type ResultKind = 'win' | 'draw' | 'loss';

export function resultKind(match: MatchSummary): ResultKind | null {
  if (!match.played || match.homeScore === null || match.awayScore === null) {
    return null;
  }
  const mine = match.isHome ? match.homeScore : match.awayScore;
  const theirs = match.isHome ? match.awayScore : match.homeScore;
  if (mine > theirs) return 'win';
  if (mine < theirs) return 'loss';
  return 'draw';
}
