import { afterEach, describe, expect, it, vi } from 'vitest';

import { ApiError, apiFetch, clearToken, getToken, setToken } from '@/lib/api';

function okResponse(body: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => body,
  });
}

describe('token helpers', () => {
  it('stores and reads the token from localStorage', () => {
    setToken('abc');

    expect(getToken()).toBe('abc');
    expect(localStorage.getItem('fm_token')).toBe('abc');
  });

  it('clears the token', () => {
    setToken('abc');
    clearToken();

    expect(getToken()).toBeNull();
  });
});

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sends the Authorization header when a token exists', async () => {
    setToken('my-token');
    const fetchMock = okResponse({});
    vi.stubGlobal('fetch', fetchMock);

    await apiFetch('/players/my-team');

    const [, options] = fetchMock.mock.calls[0];
    const headers = options.headers as Record<string, string>;
    expect(headers.Authorization).toBe('Bearer my-token');
  });

  it('omits the Authorization header when there is no token', async () => {
    const fetchMock = okResponse({});
    vi.stubGlobal('fetch', fetchMock);

    await apiFetch('/health');

    const [, options] = fetchMock.mock.calls[0];
    const headers = options.headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it('returns the parsed JSON body on success', async () => {
    const fetchMock = okResponse({ teamName: 'FC' });
    vi.stubGlobal('fetch', fetchMock);

    const data = await apiFetch<{ teamName: string }>('/players/my-team');

    expect(data).toEqual({ teamName: 'FC' });
  });

  it('throws an ApiError carrying the backend errorCode on a non-ok response', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ errorCode: 'auth.invalidCredentials' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const error = await apiFetch('/auth/login').catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.errorCode).toBe('auth.invalidCredentials');
    expect(error.status).toBe(401);
  });

  it('falls back to a generic error code when the body has none', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error('no body');
      },
    });
    vi.stubGlobal('fetch', fetchMock);

    const error = await apiFetch('/x').catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.errorCode).toBe('common.unknownError');
  });
});
