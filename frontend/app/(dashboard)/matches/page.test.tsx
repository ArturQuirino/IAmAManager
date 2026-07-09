import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { MatchDetail, MatchListResponse } from '@/lib/api';

const { replace, getMatchesMock, simulateMatchMock, getMatchMock } = vi.hoisted(
  () => ({
    replace: vi.fn(),
    getMatchesMock: vi.fn(),
    simulateMatchMock: vi.fn(),
    getMatchMock: vi.fn(),
  }),
);

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getMatches: getMatchesMock,
    simulateMatch: simulateMatchMock,
    getMatch: getMatchMock,
    getToken: () => 'token',
  };
});

import MatchesPage from '@/app/(dashboard)/matches/page';

function renderPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <MatchesPage />
    </NextIntlClientProvider>,
  );
}

function matchList(): MatchListResponse {
  return {
    matches: [
      {
        id: 'm1',
        round: 1,
        seasonNumber: 1,
        isHome: true,
        opponentTeamId: 't2',
        opponentName: 'Rivals FC',
        homeScore: null,
        awayScore: null,
        played: false,
        scheduledDate: null,
      },
    ],
  };
}

function detail(): MatchDetail {
  return {
    id: 'm1',
    round: 1,
    seasonNumber: 1,
    isHome: true,
    homeTeamId: 't1',
    homeTeamName: 'Mine FC',
    awayTeamId: 't2',
    awayTeamName: 'Rivals FC',
    homeScore: 2,
    awayScore: 1,
    played: true,
    events: [
      {
        minute: 12,
        isHome: true,
        playType: 'dribble',
        outcome: 'goal',
        player: 'Marco Silva',
        homeScore: 1,
        awayScore: 0,
      },
    ],
  };
}

beforeEach(() => {
  replace.mockClear();
  getMatchesMock.mockReset();
  simulateMatchMock.mockReset();
  getMatchMock.mockReset();
});

describe('MatchesPage', () => {
  it('lists the fixtures with round and opponent', async () => {
    getMatchesMock.mockResolvedValue(matchList());
    renderPage();

    expect(await screen.findByText('Rivals FC')).toBeInTheDocument();
    expect(screen.getByText('Rodada 1')).toBeInTheDocument();
    expect(screen.getByText('Não jogada')).toBeInTheDocument();
  });

  it('simulates a match, shows the score and opens the replay', async () => {
    getMatchesMock.mockResolvedValue(matchList());
    simulateMatchMock.mockResolvedValue(detail());
    renderPage();

    const button = await screen.findByRole('button', { name: 'Simular' });
    await userEvent.click(button);

    // Replay dialog appears with the scored event.
    expect(await screen.findByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText(/Marco Silva marca/)).toBeInTheDocument();
    expect(simulateMatchMock).toHaveBeenCalledWith('m1');
  });

  it('shows the translated error when simulation fails', async () => {
    getMatchesMock.mockResolvedValue(matchList());
    const { ApiError } = await import('@/lib/api');
    simulateMatchMock.mockRejectedValue(new ApiError('match.alreadyPlayed', 409));
    renderPage();

    const button = await screen.findByRole('button', { name: 'Simular' });
    await userEvent.click(button);

    await waitFor(() =>
      expect(screen.getByText('Essa partida já foi jogada.')).toBeInTheDocument(),
    );
  });

  it('shows the empty state when there are no matches', async () => {
    getMatchesMock.mockResolvedValue({ matches: [] });
    renderPage();

    expect(
      await screen.findByText('Nenhuma partida agendada ainda.'),
    ).toBeInTheDocument();
  });
});
