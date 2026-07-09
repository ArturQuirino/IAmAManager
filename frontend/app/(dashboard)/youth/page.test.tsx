import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';
import type { YouthCandidate, YouthResponse } from '@/lib/api';

const { replace, getYouthMock, addYouthMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getYouthMock: vi.fn(),
  addYouthMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    getYouth: getYouthMock,
    addYouthPlayer: addYouthMock,
    getToken: () => 'token',
  };
});

import { ApiError } from '@/lib/api';
import YouthPage from '@/app/(dashboard)/youth/page';

function candidate(overrides: Partial<YouthCandidate> = {}): YouthCandidate {
  return {
    id: 'c1',
    name: 'Prospect One',
    position: 'ATT',
    pace: 60,
    shooting: 55,
    passing: 50,
    dribbling: 65,
    defending: 30,
    physical: 58,
    overall: 53,
    ...overrides,
  };
}

function youth(overrides: Partial<YouthResponse> = {}): YouthResponse {
  return {
    candidates: [
      candidate(),
      candidate({ id: 'c2', name: 'Prospect Two', position: 'GK' }),
    ],
    squadSize: 26,
    maxSquadSize: 40,
    ...overrides,
  };
}

function renderYouthPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <YouthPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  getYouthMock.mockReset();
  addYouthMock.mockReset();
});

describe('YouthPage', () => {
  it('lists this week’s prospects', async () => {
    getYouthMock.mockResolvedValue(youth());
    renderYouthPage();

    expect(await screen.findByText('Prospect One')).toBeInTheDocument();
    expect(screen.getByText('Prospect Two')).toBeInTheDocument();
  });

  it('promotes a prospect and refreshes the pool', async () => {
    getYouthMock.mockResolvedValue(youth());
    addYouthMock.mockResolvedValue(
      youth({
        candidates: [candidate({ id: 'c2', name: 'Prospect Two', position: 'GK' })],
        squadSize: 27,
      }),
    );
    renderYouthPage();

    const user = userEvent.setup();
    const addButtons = await screen.findAllByRole('button', {
      name: 'Adicionar ao elenco',
    });
    await user.click(addButtons[0]);

    await waitFor(() => expect(addYouthMock).toHaveBeenCalledWith('c1'));
    await waitFor(() =>
      expect(screen.queryByText('Prospect One')).not.toBeInTheDocument(),
    );
  });

  it('disables adding when the squad is full', async () => {
    getYouthMock.mockResolvedValue(youth({ squadSize: 40, maxSquadSize: 40 }));
    renderYouthPage();

    expect(
      await screen.findByText(
        'Seu elenco está cheio. Dispense um jogador antes de adicionar uma promessa.',
      ),
    ).toBeInTheDocument();
    const addButtons = screen.getAllByRole('button', {
      name: 'Adicionar ao elenco',
    });
    addButtons.forEach((button) => expect(button).toBeDisabled());
  });

  it('shows the translated error when promotion is rejected', async () => {
    getYouthMock.mockResolvedValue(youth());
    addYouthMock.mockRejectedValue(new ApiError('squad.full', 409));
    renderYouthPage();

    const user = userEvent.setup();
    const addButtons = await screen.findAllByRole('button', {
      name: 'Adicionar ao elenco',
    });
    await user.click(addButtons[0]);

    expect(
      await screen.findByText(
        'Seu elenco está cheio (40 jogadores). Dispense um jogador primeiro.',
      ),
    ).toBeInTheDocument();
  });

  it('shows the translated load error when the request fails', async () => {
    getYouthMock.mockRejectedValue(new Error('boom'));
    renderYouthPage();

    expect(
      await screen.findByText('Erro ao carregar a base. Tente novamente.'),
    ).toBeInTheDocument();
  });
});
