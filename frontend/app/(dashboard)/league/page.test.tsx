import { render, screen } from '@testing-library/react';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { StandingsResponse } from '@/lib/api';

const { replace, getStandingsMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getStandingsMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

// A token keeps useAuth authenticated so the page fetches instead of
// redirecting; getStandings is the call under test.
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getStandings: getStandingsMock,
    getToken: () => 'token',
  };
});

import LeaguePage from '@/app/(dashboard)/league/page';

function renderLeaguePage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <LeaguePage />
    </NextIntlClientProvider>,
  );
}

function standings(
  overrides: Partial<StandingsResponse> = {},
): StandingsResponse {
  return {
    divisionLevel: 4,
    seasonNumber: 1,
    entries: [
      {
        teamId: '1',
        teamName: 'Rival FC',
        played: 3,
        wins: 3,
        draws: 0,
        losses: 0,
        goalsFor: 7,
        goalsAgainst: 1,
        goalDifference: 6,
        points: 9,
        isCurrentUserTeam: false,
      },
      {
        teamId: '2',
        teamName: 'Mine FC',
        played: 3,
        wins: 1,
        draws: 1,
        losses: 1,
        goalsFor: 4,
        goalsAgainst: 4,
        goalDifference: 0,
        points: 4,
        isCurrentUserTeam: true,
      },
    ],
    ...overrides,
  };
}

beforeEach(() => {
  replace.mockClear();
  getStandingsMock.mockReset();
});

describe('LeaguePage', () => {
  it('renders the ranked teams with their points', async () => {
    getStandingsMock.mockResolvedValue(standings());
    renderLeaguePage();

    expect(await screen.findByText('Rival FC')).toBeInTheDocument();
    expect(screen.getByText('Mine FC')).toBeInTheDocument();
    expect(screen.getByText('Divisão 4 · Temporada 1')).toBeInTheDocument();

    const rows = screen.getAllByRole('row');
    // Header row + two team rows; the leader comes first.
    expect(rows).toHaveLength(3);
    expect(rows[1]).toHaveTextContent('Rival FC');
    expect(rows[2]).toHaveTextContent('Mine FC');
  });

  it('highlights the signed-in manager’s team', async () => {
    getStandingsMock.mockResolvedValue(standings());
    renderLeaguePage();

    const ownRow = (await screen.findByText('Mine FC')).closest('td');
    expect(ownRow).toHaveClass('text-accent');
  });

  it('shows an empty-state message when the team has no division', async () => {
    getStandingsMock.mockResolvedValue(
      standings({ divisionLevel: null, seasonNumber: null, entries: [] }),
    );
    renderLeaguePage();

    expect(
      await screen.findByText('Seu time ainda não está em uma divisão.'),
    ).toBeInTheDocument();
  });

  it('shows the translated error when the request fails', async () => {
    getStandingsMock.mockRejectedValue(new Error('boom'));
    renderLeaguePage();

    expect(
      await screen.findByText('Erro ao carregar a tabela. Tente novamente.'),
    ).toBeInTheDocument();
  });
});
