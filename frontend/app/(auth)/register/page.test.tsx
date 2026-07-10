import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';

const { replace, registerMock, setTokenMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  registerMock: vi.fn(),
  setTokenMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

// getToken is used by useRedirectIfAuthenticated (rendered by the page).
// Returning null keeps that redirect effect inert during these tests.
// ApiError/UNKNOWN_ERROR_CODE come from the real module so `instanceof`
// checks in the page component still work against the mocked rejections.
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    register: registerMock,
    setToken: setTokenMock,
    getToken: () => null,
  };
});

import { ApiError } from '@/lib/api';
import RegisterPage from '@/app/(auth)/register/page';

function renderRegisterPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <RegisterPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  registerMock.mockReset();
  setTokenMock.mockClear();
});

async function fillAndSubmit(
  email = 'user@example.com',
  password = 'secret123',
  teamName = 'Newcomer FC',
) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Nome do time'), teamName);
  await user.type(screen.getByLabelText('Email'), email);
  await user.type(screen.getByLabelText('Senha'), password);
  await user.click(screen.getByRole('button', { name: 'Criar time' }));
  return user;
}

describe('RegisterPage', () => {
  it('registers and redirects to /home on success', async () => {
    registerMock.mockResolvedValue({ access_token: 'jwt-123' });
    renderRegisterPage();

    await fillAndSubmit();

    await waitFor(() =>
      expect(setTokenMock).toHaveBeenCalledWith('jwt-123'),
    );
    expect(registerMock).toHaveBeenCalledWith(
      'user@example.com',
      'secret123',
      'Newcomer FC',
    );
    expect(replace).toHaveBeenCalledWith('/home');
  });

  it('shows the translated message for a known backend error code', async () => {
    registerMock.mockRejectedValue(
      new ApiError('auth.emailAlreadyExists', 409),
    );
    renderRegisterPage();

    await fillAndSubmit();

    expect(
      await screen.findByText('Este email já está cadastrado. Tente entrar.'),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it('falls back to a generic message for an unrecognized error', async () => {
    registerMock.mockRejectedValue(new Error('network down'));
    renderRegisterPage();

    await fillAndSubmit();

    expect(
      await screen.findByText('Ocorreu um erro. Tente novamente.'),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
