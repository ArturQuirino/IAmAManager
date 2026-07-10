import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NextIntlClientProvider } from 'next-intl';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import messages from '@/messages/pt.json';

const { replace, loginMock, setTokenMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  loginMock: vi.fn(),
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
    login: loginMock,
    setToken: setTokenMock,
    getToken: () => null,
  };
});

import { ApiError } from '@/lib/api';
import LoginPage from '@/app/(auth)/login/page';

function renderLoginPage() {
  return render(
    <NextIntlClientProvider locale="pt" messages={messages}>
      <LoginPage />
    </NextIntlClientProvider>,
  );
}

beforeEach(() => {
  replace.mockClear();
  loginMock.mockReset();
  setTokenMock.mockClear();
});

async function fillAndSubmit(
  email = 'user@example.com',
  password = 'secret123',
) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email'), email);
  await user.type(screen.getByLabelText('Senha'), password);
  await user.click(screen.getByRole('button', { name: 'Entrar' }));
  return user;
}

describe('LoginPage', () => {
  it('logs in and redirects to /home on success', async () => {
    loginMock.mockResolvedValue({ access_token: 'jwt-123' });
    renderLoginPage();

    await fillAndSubmit();

    await waitFor(() =>
      expect(setTokenMock).toHaveBeenCalledWith('jwt-123'),
    );
    expect(loginMock).toHaveBeenCalledWith('user@example.com', 'secret123');
    expect(replace).toHaveBeenCalledWith('/home');
  });

  it('shows the translated message for a known backend error code', async () => {
    loginMock.mockRejectedValue(
      new ApiError('auth.invalidCredentials', 401),
    );
    renderLoginPage();

    await fillAndSubmit();

    expect(
      await screen.findByText('Credenciais inválidas. Tente novamente.'),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it('falls back to a generic message for an unrecognized error', async () => {
    loginMock.mockRejectedValue(new Error('network down'));
    renderLoginPage();

    await fillAndSubmit();

    expect(
      await screen.findByText('Ocorreu um erro. Tente novamente.'),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it('disables the button and shows "Entrando..." while submitting', async () => {
    let resolveLogin: (value: { access_token: string }) => void = () => {};
    loginMock.mockReturnValue(
      new Promise((resolve) => {
        resolveLogin = resolve;
      }),
    );
    renderLoginPage();

    await fillAndSubmit();

    const submittingButton = await screen.findByRole('button', {
      name: 'Entrando...',
    });
    expect(submittingButton).toBeDisabled();

    // Resolve so the pending state settles and no act() warning is emitted.
    resolveLogin({ access_token: 'jwt-123' });
    await waitFor(() => expect(setTokenMock).toHaveBeenCalled());
  });
});
