import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

// jsdom has no DataTransfer; a stub carrying the dragged id is enough.
function dataTransfer(id: string) {
  return {
    setData: vi.fn(),
    getData: () => id,
    effectAllowed: '',
    dropEffect: '',
  };
}

// The drop handler normalizes clientX/Y against the pitch rect; jsdom
// reports a zero-sized rect, so pin it to a 100x100 box.
function mockPitchRect(pitchEl: HTMLElement) {
  pitchEl.getBoundingClientRect = () =>
    ({
      left: 0,
      top: 0,
      width: 100,
      height: 100,
      right: 100,
      bottom: 100,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    }) as DOMRect;
}

async function loadPage() {
  renderTacticsPage();
  const pitch = await screen.findByRole('region', { name: 'Campo' });
  mockPitchRect(pitch);
  const bench = screen.getByRole('region', { name: 'Banco de reservas' });
  return { pitch, bench };
}

function dragAndDrop(
  chip: HTMLElement,
  target: HTMLElement,
  playerId: string,
  at: { x: number; y: number } = { x: 0, y: 0 },
) {
  const transfer = dataTransfer(playerId);
  fireEvent.dragStart(chip, { dataTransfer: transfer });
  // jsdom has no DragEvent, and the plain-Event fallback drops clientX/Y;
  // a MouseEvent named "drop" carries the coordinates and reaches React.
  const drop = new MouseEvent('drop', {
    bubbles: true,
    cancelable: true,
    clientX: at.x,
    clientY: at.y,
  });
  Object.defineProperty(drop, 'dataTransfer', { value: transfer });
  fireEvent(target, drop);
}

beforeEach(() => {
  replace.mockClear();
  getTacticsMock.mockReset();
  setStartingXiMock.mockReset();
  // Auto-save fires on any valid change; default to a resolving stub so tests
  // that only assert on the pitch don't trip on an unhandled rejection.
  setStartingXiMock.mockResolvedValue(tactics());
});

describe('TacticsPage', () => {
  it('arranges the starters on the pitch and the rest on the bench', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    const { pitch, bench } = await loadPage();

    expect(within(pitch).getByLabelText('Keeper')).toBeInTheDocument();
    expect(within(pitch).getByLabelText('Defender 0')).toBeInTheDocument();
    expect(within(bench).getByLabelText('Backup Keeper')).toBeInTheDocument();
    expect(within(bench).getByLabelText('Reserve Mid')).toBeInTheDocument();
    expect(screen.getByText('4-3-3')).toBeInTheDocument();
    expect(screen.getByText('11/11')).toBeInTheDocument();
  });

  it('auto-saves the eleven when the lineup changes, without a save button', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    setStartingXiMock.mockResolvedValue(tactics());
    const { pitch, bench } = await loadPage();

    expect(
      screen.queryByRole('button', { name: 'Salvar escalação' }),
    ).not.toBeInTheDocument();
    // A valid swap keeps eleven on the pitch and should persist on its own.
    dragAndDrop(
      within(bench).getByLabelText('Reserve Mid'),
      pitch,
      'bench-mid',
      { x: 34, y: 44 },
    );

    await waitFor(() => expect(setStartingXiMock).toHaveBeenCalledTimes(1));
    expect(setStartingXiMock.mock.calls[0][0]).toHaveLength(11);
    expect(await screen.findByText('Escalação salva.')).toBeInTheDocument();
  });

  it('does not auto-save while the lineup is incomplete', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    const { pitch, bench } = await loadPage();

    dragAndDrop(within(pitch).getByLabelText('Attacker 0'), bench, 'att0');

    expect(within(bench).getByLabelText('Attacker 0')).toBeInTheDocument();
    expect(screen.getByText('10/11')).toBeInTheDocument();
    await waitFor(() => expect(setStartingXiMock).not.toHaveBeenCalled());
  });

  it('replaces the occupant when a bench player is dropped on them', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    const { pitch, bench } = await loadPage();

    // With three midfielders centered, Midfielder 0 sits at x=34%, y=44%.
    dragAndDrop(
      within(bench).getByLabelText('Reserve Mid'),
      pitch,
      'bench-mid',
      { x: 34, y: 44 },
    );

    expect(within(pitch).getByLabelText('Reserve Mid')).toBeInTheDocument();
    expect(within(bench).getByLabelText('Midfielder 0')).toBeInTheDocument();
    expect(screen.getByText('11/11')).toBeInTheDocument();
  });

  it('rejects a goalkeeper dropped outside the goal', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    const { pitch, bench } = await loadPage();

    dragAndDrop(
      within(bench).getByLabelText('Backup Keeper'),
      pitch,
      'bench-gk',
      { x: 50, y: 44 },
    );

    expect(
      screen.getByText(
        'Apenas o goleiro pode ocupar o gol, e o goleiro não pode jogar na linha.',
      ),
    ).toBeInTheDocument();
    expect(within(bench).getByLabelText('Backup Keeper')).toBeInTheDocument();
    expect(screen.getByText('11/11')).toBeInTheDocument();
  });

  it('shows the translated error when the server rejects the lineup', async () => {
    getTacticsMock.mockResolvedValue(tactics());
    setStartingXiMock.mockRejectedValue(
      new ApiError('tactics.needExactlyOneGk', 422),
    );
    const { pitch, bench } = await loadPage();

    dragAndDrop(
      within(bench).getByLabelText('Reserve Mid'),
      pitch,
      'bench-mid',
      { x: 34, y: 44 },
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
