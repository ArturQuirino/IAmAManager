import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

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
vi.mock('@/lib/api', () => ({
  login: loginMock,
  setToken: setTokenMock,
  getToken: () => null,
}));

import LoginPage from '@/app/(auth)/login/page';

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
  it('logs in and redirects to /team on success', async () => {
    loginMock.mockResolvedValue({ access_token: 'jwt-123' });
    render(<LoginPage />);

    await fillAndSubmit();

    await waitFor(() =>
      expect(setTokenMock).toHaveBeenCalledWith('jwt-123'),
    );
    expect(loginMock).toHaveBeenCalledWith('user@example.com', 'secret123');
    expect(replace).toHaveBeenCalledWith('/team');
  });

  it('shows a Portuguese error message on failure', async () => {
    loginMock.mockRejectedValue(new Error('bad credentials'));
    render(<LoginPage />);

    await fillAndSubmit();

    expect(
      await screen.findByText('Credenciais inválidas. Tente novamente.'),
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
    render(<LoginPage />);

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
