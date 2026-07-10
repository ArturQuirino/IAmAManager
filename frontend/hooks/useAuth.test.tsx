import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// vi.mock is hoisted above imports, so the mock functions it references must
// be created with vi.hoisted (they cannot close over ordinary top-level vars).
const { replace, getTokenMock } = vi.hoisted(() => ({
  replace: vi.fn(),
  getTokenMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

vi.mock('@/lib/api', () => ({
  getToken: getTokenMock,
}));

import { useAuth, useRedirectIfAuthenticated } from '@/hooks/useAuth';

beforeEach(() => {
  replace.mockClear();
  getTokenMock.mockReset();
});

describe('useAuth', () => {
  it('redirects to /login when there is no token', async () => {
    getTokenMock.mockReturnValue(null);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
    expect(replace).toHaveBeenCalledWith('/login');
  });

  it('is authenticated when a token exists', async () => {
    getTokenMock.mockReturnValue('token');

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));
    expect(replace).not.toHaveBeenCalled();
  });

  it('does not redirect when redirectToLogin is false', async () => {
    getTokenMock.mockReturnValue(null);

    const { result } = renderHook(() => useAuth(false));

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
    expect(replace).not.toHaveBeenCalled();
  });
});

describe('useRedirectIfAuthenticated', () => {
  it('redirects to /home when a token exists', async () => {
    getTokenMock.mockReturnValue('token');

    renderHook(() => useRedirectIfAuthenticated());

    await waitFor(() => expect(replace).toHaveBeenCalledWith('/home'));
  });

  it('does nothing when there is no token', async () => {
    getTokenMock.mockReturnValue(null);

    renderHook(() => useRedirectIfAuthenticated());

    await waitFor(() => expect(getTokenMock).toHaveBeenCalled());
    expect(replace).not.toHaveBeenCalled();
  });
});
