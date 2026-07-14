import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { TeamInfo } from '@/lib/api';

const { replace, getTeamInfoMock, updateTeamNameMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getTeamInfoMock: vi.fn(),
  updateTeamNameMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getTeamInfo: getTeamInfoMock,
    updateTeamName: updateTeamNameMock,
    getToken: () => 'token',
  };
});

import { ApiError } from '@/lib/api';
import TeamPage from '@/app/(dashboard)/team/page';

function teamInfo(overrides: Partial<TeamInfo> = {}): TeamInfo {
  return {
    teamName: 'Owner FC',
    divisionLevel: 3,
    seasonNumber: 2,
    played: 5,
    wins: 3,
    draws: 0,
    losses: 2,
    goalsFor: 8,
    goalsAgainst: 5,
    goalDifference: 3,
    points: 9,
    playersCount: 11,
    ...overrides,
  };
}

function renderTeamPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <TeamPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  getTeamInfoMock.mockReset();
  updateTeamNameMock.mockReset();
});

describe('TeamPage', () => {
  it('shows the current team name and season overview', async () => {
    getTeamInfoMock.mockResolvedValue(teamInfo());
    renderTeamPage();

    expect(await screen.findByDisplayValue('Owner FC')).toBeInTheDocument();
    expect(screen.getByText('Divisão 3 · Temporada 2')).toBeInTheDocument();
    // Players count.
    expect(screen.getByText('11')).toBeInTheDocument();
  });

  it('saves a new team name and reflects the update', async () => {
    getTeamInfoMock.mockResolvedValue(teamInfo());
    updateTeamNameMock.mockResolvedValue(teamInfo({ teamName: 'New FC' }));
    renderTeamPage();

    const input = await screen.findByDisplayValue('Owner FC');
    const user = userEvent.setup();
    await user.clear(input);
    await user.type(input, 'New FC');
    await user.click(screen.getByRole('button', { name: 'Salvar alterações' }));

    await waitFor(() =>
      expect(updateTeamNameMock).toHaveBeenCalledWith('New FC'),
    );
    expect(
      await screen.findByText('Nome do time atualizado.'),
    ).toBeInTheDocument();
  });

  it('shows the translated error when the name is already taken', async () => {
    getTeamInfoMock.mockResolvedValue(teamInfo());
    updateTeamNameMock.mockRejectedValue(
      new ApiError('team.nameAlreadyExists', 409),
    );
    renderTeamPage();

    const input = await screen.findByDisplayValue('Owner FC');
    const user = userEvent.setup();
    await user.clear(input);
    await user.type(input, 'Taken FC');
    await user.click(screen.getByRole('button', { name: 'Salvar alterações' }));

    expect(
      await screen.findByText(
        'Este nome de time já está em uso. Escolha outro.',
      ),
    ).toBeInTheDocument();
  });

  it('disables saving while the name is unchanged', async () => {
    getTeamInfoMock.mockResolvedValue(teamInfo());
    renderTeamPage();

    await screen.findByDisplayValue('Owner FC');
    expect(
      screen.getByRole('button', { name: 'Salvar alterações' }),
    ).toBeDisabled();
  });

  it('shows the translated load error when the request fails', async () => {
    getTeamInfoMock.mockRejectedValue(new Error('boom'));
    renderTeamPage();

    expect(
      await screen.findByText(
        'Erro ao carregar o time. Tente fazer login novamente.',
      ),
    ).toBeInTheDocument();
  });
});
