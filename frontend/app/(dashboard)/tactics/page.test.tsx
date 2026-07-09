import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { Player, PlayerPosition, TacticsResponse } from '@/lib/api';

const { replace, getTacticsMock, setStartingXiMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getTacticsMock: vi.fn(),
  setStartingXiMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getTactics: getTacticsMock,
    setStartingXi: setStartingXiMock,
    getToken: () => 'token',
  };
});

import { ApiError } from '@/lib/api';
import TacticsPage from '@/app/(dashboard)/tactics/page';

function player(
  id: string,
  name: string,
  position: PlayerPosition,
): Player {
  return {
    id,
    name,
    position,
    pace: 70,
    shooting: 70,
    passing: 70,
    dribbling: 70,
    defending: 70,
    physical: 70,
    overall: 70,
  };
}

// A valid starting XI: 1 GK + 4 DEF + 3 MID + 3 ATT (a 4-3-3).
function startingXi(): Player[] {
  const players = [player('gk1', 'Keeper', 'GK')];
  for (let i = 0; i < 4; i += 1)
    players.push(player(`def${i}`, `Defender ${i}`, 'DEF'));
  for (let i = 0; i < 3; i += 1)
    players.push(player(`mid${i}`, `Midfielder ${i}`, 'MID'));
  for (let i = 0; i < 3; i += 1)
    players.push(player(`att${i}`, `Attacker ${i}`, 'ATT'));
  return players;
}

function tactics(overrides: Partial<TacticsResponse> = {}): TacticsResponse {
  return {
    formation: '4-3-3',
    starters: startingXi(),
    bench: [
      player('bench-gk', 'Backup Keeper', 'GK'),
      player('bench-mid', 'Reserve Mid', 'MID'),
    ],
    ...overrides,
  };
}

function renderTacticsPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <TacticsPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  getTacticsMock.mockReset();
  setStartingXiMock.mockReset();
});

describe('TacticsPage', () => {
  it('lists the whole squad and shows the derived formation', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    renderTacticsPage();

    expect(await screen.findByText('Keeper')).toBeInTheDocument();
    expect(screen.getByText('Backup Keeper')).toBeInTheDocument();
    // Both the initial starters and the toggled selection derive "4-3-3".
    expect(screen.getByText('4-3-3')).toBeInTheDocument();
    // Starters come pre-checked.
    expect(screen.getByRole('checkbox', { name: 'Keeper' })).toBeChecked();
    expect(
      screen.getByRole('checkbox', { name: 'Backup Keeper' }),
    ).not.toBeChecked();
  });

  it('saves the selected eleven', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    setStartingXiMock.mockResolvedValue(tactics());
    renderTacticsPage();

    const user = userEvent.setup();
    const save = await screen.findByRole('button', {
      name: 'Salvar escalação',
    });
    expect(save).toBeEnabled();
    await user.click(save);

    await waitFor(() => expect(setStartingXiMock).toHaveBeenCalledTimes(1));
    expect(setStartingXiMock.mock.calls[0][0]).toHaveLength(11);
    expect(await screen.findByText('Escalação salva.')).toBeInTheDocument();
  });

  it('disables saving while the selection is not exactly eleven', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    renderTacticsPage();

    const user = userEvent.setup();
    // Drop a starter: the selection falls to ten and saving is blocked.
    await user.click(await screen.findByRole('checkbox', { name: 'Keeper' }));

    expect(
      screen.getByRole('button', { name: 'Salvar escalação' }),
    ).toBeDisabled();
  });

  it('disables saving when there is not exactly one goalkeeper', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    renderTacticsPage();

    const user = userEvent.setup();
    // Swap an outfielder for the backup keeper: 11 players but two keepers.
    await user.click(
      await screen.findByRole('checkbox', { name: 'Attacker 0' }),
    );
    await user.click(screen.getByRole('checkbox', { name: 'Backup Keeper' }));

    expect(
      screen.getByRole('button', { name: 'Salvar escalação' }),
    ).toBeDisabled();
  });

  it('shows the translated error when the server rejects the lineup', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    setStartingXiMock.mockRejectedValue(
      new ApiError('tactics.needExactlyOneGk', 422),
    );
    renderTacticsPage();

    const user = userEvent.setup();
    await user.click(
      await screen.findByRole('button', { name: 'Salvar escalação' }),
    );

    expect(
      await screen.findByText(
        'Sua escalação titular deve ter exatamente um goleiro.',
      ),
    ).toBeInTheDocument();
  });

  it('shows the translated load error when the request fails', async () => {
    getTacticsMock.mockRejectedValue(new Error('boom'));
    renderTacticsPage();

    expect(
      await screen.findByText('Erro ao carregar a tática. Tente novamente.'),
    ).toBeInTheDocument();
  });
});
