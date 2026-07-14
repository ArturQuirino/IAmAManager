const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// Falls back to this key (a path into the "errors" namespace) whenever the
// backend response doesn't carry a recognized errorCode, e.g. network
// failures or unhandled 5xx/422 responses.
export const UNKNOWN_ERROR_CODE = 'common.unknownError';

export class ApiError extends Error {
  constructor(
    public readonly errorCode: string,
    public readonly status: number,
  ) {
    super(errorCode);
    this.name = 'ApiError';
  }
}

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
    const body = await response.json().catch(() => ({}));
    const errorCode =
      typeof body.errorCode === 'string' ? body.errorCode : UNKNOWN_ERROR_CODE;
    throw new ApiError(errorCode, response.status);
  }

  return response.json();
}

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  email: string,
  password: string,
  teamName: string,
) {
  return apiFetch<{ access_token: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, teamName }),
  });
}

export type PlayerPosition = 'GK' | 'DEF' | 'MID' | 'ATT';

export interface Player {
  id: string;
  name: string;
  position: PlayerPosition;
  pace: number;
  shooting: number;
  passing: number;
  dribbling: number;
  defending: number;
  physical: number;
  overall: number;
}

export interface TeamInfo {
  teamName: string;
  // Null while the team has not been placed in a division yet.
  divisionLevel: number | null;
  seasonNumber: number | null;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  playersCount: number;
}

export async function getTeamInfo(): Promise<TeamInfo> {
  return apiFetch<TeamInfo>('/team');
}

// Renaming returns the refreshed team info, so the caller can update the screen
// in a single round-trip. Throws ApiError('team.nameAlreadyExists') on a clash.
export async function updateTeamName(teamName: string): Promise<TeamInfo> {
  return apiFetch<TeamInfo>('/team', {
    method: 'PATCH',
    body: JSON.stringify({ teamName }),
  });
}

export interface StandingEntry {
  teamId: string;
  teamName: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  isCurrentUserTeam: boolean;
}

export interface StandingsResponse {
  // Null when the team has not been placed in a division yet.
  divisionLevel: number | null;
  seasonNumber: number | null;
  entries: StandingEntry[];
}

export async function getStandings(): Promise<StandingsResponse> {
  return apiFetch<StandingsResponse>('/competition/standings');
}

export interface SquadResponse {
  teamName: string;
  players: Player[];
}

export async function getSquad(): Promise<SquadResponse> {
  return apiFetch<SquadResponse>('/squad');
}

// Removing a player returns the updated squad, so the caller can refresh in a
// single round-trip.
export async function removePlayer(playerId: string): Promise<SquadResponse> {
  return apiFetch<SquadResponse>(`/squad/players/${playerId}`, {
    method: 'DELETE',
  });
}

export interface TacticsResponse {
  // Outfield shape of the current XI (e.g. "4-3-3"); null when none is set.
  formation: string | null;
  starters: Player[];
  bench: Player[];
}

export async function getTactics(): Promise<TacticsResponse> {
  return apiFetch<TacticsResponse>('/tactics');
}

// Persisting the starting XI returns the updated starters/bench (and derived
// formation), so the caller can refresh in a single round-trip.
export async function setStartingXi(
  playerIds: string[],
): Promise<TacticsResponse> {
  return apiFetch<TacticsResponse>('/tactics/starting-xi', {
    method: 'PUT',
    body: JSON.stringify({ playerIds }),
  });
}

// A youth prospect shares the player shape; it becomes a Player unchanged when
// promoted into the squad.
export type YouthCandidate = Player;

export interface YouthResponse {
  candidates: YouthCandidate[];
  squadSize: number;
  maxSquadSize: number;
}

export async function getYouth(): Promise<YouthResponse> {
  return apiFetch<YouthResponse>('/youth');
}

// Adding a prospect returns the refreshed pool (and squad size), so the caller
// can update the page without a second request.
export async function addYouthPlayer(
  candidateId: string,
): Promise<YouthResponse> {
  return apiFetch<YouthResponse>(`/youth/${candidateId}/add`, {
    method: 'POST',
  });
}

export interface MatchSummary {
  id: string;
  round: number;
  seasonNumber: number;
  // From the signed-in team's perspective.
  isHome: boolean;
  opponentTeamId: string;
  opponentName: string;
  // Null until the match has been played.
  homeScore: number | null;
  awayScore: number | null;
  played: boolean;
  scheduledDate: string | null;
}

export interface MatchListResponse {
  matches: MatchSummary[];
}

export interface MatchEvent {
  minute: number;
  isHome: boolean;
  playType: string;
  // Stable outcome code (e.g. "goal", "saved"), translated on the client.
  outcome: string;
  player: string;
  homeScore: number;
  awayScore: number;
}

export interface MatchDetail {
  id: string;
  round: number;
  seasonNumber: number;
  isHome: boolean;
  homeTeamId: string;
  homeTeamName: string;
  awayTeamId: string;
  awayTeamName: string;
  homeScore: number | null;
  awayScore: number | null;
  played: boolean;
  events: MatchEvent[];
}

export async function getMatches(): Promise<MatchListResponse> {
  return apiFetch<MatchListResponse>('/matches');
}

export async function getMatch(matchId: string): Promise<MatchDetail> {
  return apiFetch<MatchDetail>(`/matches/${matchId}`);
}

// Simulating a match returns its full detail (score + minute-by-minute events),
// so the caller can show the result and replay without a second request.
export async function simulateMatch(matchId: string): Promise<MatchDetail> {
  return apiFetch<MatchDetail>(`/matches/${matchId}/simulate`, {
    method: 'POST',
  });
}
