import { render, screen } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { MatchListResponse, StandingsResponse } from '@/lib/api';

const { replace, getMatchesMock, getStandingsMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getMatchesMock: vi.fn(),
  getStandingsMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getMatches: getMatchesMock,
    getStandings: getStandingsMock,
    getToken: () => 'token',
  };
});

import HomePage from '@/app/(dashboard)/home/page';

function renderHomePage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <HomePage />
    </NextIntlClientProvider>,
  );
}

function matchesResponse(): MatchListResponse {
  return {
    matches: [
      {
        id: 'a',
        round: 1,
        seasonNumber: 1,
        isHome: true,
        opponentTeamId: 'x',
        opponentName: 'Old Rovers',
        homeScore: 2,
        awayScore: 0,
        played: true,
        scheduledDate: null,
      },
      {
        id: 'b',
        round: 2,
        seasonNumber: 1,
        isHome: false,
        opponentTeamId: 'y',
        opponentName: 'North City',
        homeScore: null,
        awayScore: null,
        played: false,
        scheduledDate: null,
      },
    ],
  };
}

function standingsResponse(): StandingsResponse {
  return {
    divisionLevel: 4,
    seasonNumber: 1,
    entries: [
      {
        teamId: '1',
        teamName: 'Old Rovers',
        played: 1,
        wins: 0,
        draws: 0,
        losses: 1,
        goalsFor: 0,
        goalsAgainst: 2,
        goalDifference: -2,
        points: 0,
        isCurrentUserTeam: false,
      },
      {
        teamId: '2',
        teamName: 'Mine FC',
        played: 1,
        wins: 1,
        draws: 0,
        losses: 0,
        goalsFor: 2,
        goalsAgainst: 0,
        goalDifference: 2,
        points: 3,
        isCurrentUserTeam: true,
      },
    ],
  };
}

beforeEach(() => {
  replace.mockClear();
  getMatchesMock.mockReset();
  getStandingsMock.mockReset();
});

describe('HomePage', () => {
  it('shows the next fixture, league position and recent results', async () => {
    getMatchesMock.mockResolvedValue(matchesResponse());
    getStandingsMock.mockResolvedValue(standingsResponse());

    renderHomePage();

    // Next match is the unplayed round-2 away fixture.
    expect(await screen.findByText('North City')).toBeInTheDocument();
    expect(screen.getByText('Rodada 2')).toBeInTheDocument();
    // League position: 2nd of 2.
    expect(screen.getByText('2 de 2')).toBeInTheDocument();
    // Recent result against Old Rovers (a 2–0 win).
    expect(screen.getByText('Old Rovers')).toBeInTheDocument();
    expect(screen.getByText('2–0')).toBeInTheDocument();
  });

  it('shows the season-over message when there is no next match', async () => {
    getMatchesMock.mockResolvedValue({
      matches: matchesResponse().matches.map((m) => ({
        ...m,
        played: true,
        homeScore: 1,
        awayScore: 1,
      })),
    });
    getStandingsMock.mockResolvedValue(standingsResponse());

    renderHomePage();

    expect(
      await screen.findByText('Sem partidas futuras — a temporada acabou.'),
    ).toBeInTheDocument();
  });

  it('shows the translated error when a request fails', async () => {
    getMatchesMock.mockRejectedValue(new Error('boom'));
    getStandingsMock.mockResolvedValue(standingsResponse());

    renderHomePage();

    expect(
      await screen.findByText('Erro ao carregar o painel. Tente novamente.'),
    ).toBeInTheDocument();
  });
});
