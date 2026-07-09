import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { Player, SquadResponse } from '@/lib/api';

const { replace, getSquadMock, removePlayerMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getSquadMock: vi.fn(),
  removePlayerMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getSquad: getSquadMock,
    removePlayer: removePlayerMock,
    getToken: () => 'token',
  };
});

import { ApiError } from '@/lib/api';
import SquadPage from '@/app/(dashboard)/squad/page';

function player(overrides: Partial<Player> = {}): Player {
  return {
    id: 'p1',
    name: 'Zico',
    position: 'MID',
    pace: 70,
    shooting: 80,
    passing: 90,
    dribbling: 85,
    defending: 40,
    physical: 65,
    overall: 72,
    ...overrides,
  };
}

function squad(players: Player[]): SquadResponse {
  return { teamName: 'Owner FC', players };
}

function renderSquadPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <SquadPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  getSquadMock.mockReset();
  removePlayerMock.mockReset();
});

describe('SquadPage', () => {
  it('lists the squad players', async () => {
    getSquadMock.mockResolvedValue(
      squad([player(), player({ id: 'p2', name: 'Falcao' })]),
    );
    renderSquadPage();

    expect(await screen.findByText('Zico')).toBeInTheDocument();
    expect(screen.getByText('Falcao')).toBeInTheDocument();
  });

  it('opens the player detail with the six attributes', async () => {
    getSquadMock.mockResolvedValue(squad([player()]));
    renderSquadPage();

    const user = userEvent.setup();
    await user.click(await screen.findByText('Zico'));

    expect(screen.getByText('Detalhes do jogador')).toBeInTheDocument();
    // Passing attribute value is shown in the detail panel.
    expect(screen.getByText('90')).toBeInTheDocument();
  });

  it('removes a player after confirmation', async () => {
    getSquadMock.mockResolvedValue(
      squad([player(), player({ id: 'p2', name: 'Falcao' })]),
    );
    removePlayerMock.mockResolvedValue(squad([player({ id: 'p2', name: 'Falcao' })]));
    renderSquadPage();

    const user = userEvent.setup();
    await user.click((await screen.findAllByText('Dispensar'))[0]);
    // Confirm inside the dialog (both the row and the dialog say "Dispensar").
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Dispensar' }));

    await waitFor(() =>
      expect(removePlayerMock).toHaveBeenCalledWith('p1'),
    );
    await waitFor(() => expect(screen.queryByText('Zico')).not.toBeInTheDocument());
  });

  it('shows the translated error when a removal breaks a minimum', async () => {
    getSquadMock.mockResolvedValue(squad([player({ position: 'GK' })]));
    removePlayerMock.mockRejectedValue(new ApiError('squad.minGoalkeeper', 409));
    renderSquadPage();

    const user = userEvent.setup();
    await user.click(await screen.findByText('Dispensar'));
    const dialog = screen.getByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: 'Dispensar' }));

    expect(
      await screen.findByText('Você precisa manter pelo menos um goleiro.'),
    ).toBeInTheDocument();
  });

  it('shows the translated load error when the request fails', async () => {
    getSquadMock.mockRejectedValue(new Error('boom'));
    renderSquadPage();

    expect(
      await screen.findByText('Erro ao carregar o elenco. Tente novamente.'),
    ).toBeInTheDocument();
  });
});
