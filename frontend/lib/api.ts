const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('fm_token');
}

export function setToken(token: string): void {
  localStorage.setItem('fm_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('fm_token');
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Erro na requisição');
  }

  return response.json();
}

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export interface Player {
  id: string;
  name: string;
  position: string;
  shirtNumber: number;
  age: number;
  nationality: string;
  overall: number;
}

export interface TeamResponse {
  teamName: string;
  players: Player[];
}

export async function getMyTeam(): Promise<TeamResponse> {
  return apiFetch<TeamResponse>('/players/my-team');
}
