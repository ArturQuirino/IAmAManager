import { describe, expect, it } from 'vitest';
import type { MatchSummary, StandingsResponse } from '@/lib/api';
import { deriveHomeSummary, RECENT_RESULTS_LIMIT, resultKind } from '@/lib/home';

function match(overrides: Partial<MatchSummary> = {}): MatchSummary {
  return {
    id: 'm',
    round: 1,
    seasonNumber: 1,
    isHome: true,
    opponentTeamId: 'o',
    opponentName: 'Rival FC',
    homeScore: null,
    awayScore: null,
    played: false,
    scheduledDate: null,
    ...overrides,
  };
}

function standings(
  overrides: Partial<StandingsResponse> = {},
): StandingsResponse {
  return {
    divisionLevel: 3,
    seasonNumber: 2,
    entries: [
      {
        teamId: '1',
        teamName: 'Leader',
        played: 3,
        wins: 3,
        draws: 0,
        losses: 0,
        goalsFor: 6,
        goalsAgainst: 1,
        goalDifference: 5,
        points: 9,
        isCurrentUserTeam: false,
      },
      {
        teamId: '2',
        teamName: 'Mine',
        played: 3,
        wins: 1,
        draws: 1,
        losses: 1,
        goalsFor: 3,
        goalsAgainst: 3,
        goalDifference: 0,
        points: 4,
        isCurrentUserTeam: true,
      },
    ],
    ...overrides,
  };
}

describe('deriveHomeSummary', () => {
  it('picks the first unplayed fixture as the next match', () => {
    const matches = [
      match({ id: 'a', round: 1, played: true, homeScore: 1, awayScore: 0 }),
      match({ id: 'b', round: 2, played: false }),
      match({ id: 'c', round: 3, played: false }),
    ];

    const summary = deriveHomeSummary(matches, standings());

    expect(summary.nextMatch?.id).toBe('b');
  });

  it('returns no next match once every fixture is played', () => {
    const matches = [
      match({ id: 'a', round: 1, played: true, homeScore: 2, awayScore: 2 }),
    ];

    expect(deriveHomeSummary(matches, standings()).nextMatch).toBeNull();
  });

  it('lists recent results most-recent first, capped at the limit', () => {
    const matches = Array.from({ length: RECENT_RESULTS_LIMIT + 2 }, (_, i) =>
      match({
        id: `p${i}`,
        round: i + 1,
        played: true,
        homeScore: 1,
        awayScore: 0,
      }),
    );

    const results = deriveHomeSummary(matches, standings()).recentResults;

    expect(results).toHaveLength(RECENT_RESULTS_LIMIT);
    // Highest round first.
    expect(results[0].round).toBe(RECENT_RESULTS_LIMIT + 2);
  });

  it('reports the 1-based league position of the signed-in team', () => {
    const summary = deriveHomeSummary([], standings());

    expect(summary.position).toBe(2);
    expect(summary.totalTeams).toBe(2);
    expect(summary.divisionLevel).toBe(3);
    expect(summary.seasonNumber).toBe(2);
  });

  it('reports a null position when the team is unplaced', () => {
    const summary = deriveHomeSummary(
      [],
      standings({ divisionLevel: null, seasonNumber: null, entries: [] }),
    );

    expect(summary.position).toBeNull();
    expect(summary.totalTeams).toBe(0);
  });
});

describe('resultKind', () => {
  it('classifies a win, draw and loss from the team perspective', () => {
    expect(
      resultKind(match({ played: true, isHome: true, homeScore: 2, awayScore: 1 })),
    ).toBe('win');
    expect(
      resultKind(match({ played: true, isHome: false, homeScore: 2, awayScore: 1 })),
    ).toBe('loss');
    expect(
      resultKind(match({ played: true, homeScore: 1, awayScore: 1 })),
    ).toBe('draw');
  });

  it('returns null for an unplayed match', () => {
    expect(resultKind(match({ played: false }))).toBeNull();
  });
});
