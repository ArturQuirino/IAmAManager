'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  ApiError,
  getMatch,
  getMatches,
  MatchDetail,
  MatchSummary,
  simulateMatch,
  UNKNOWN_ERROR_CODE,
} from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

export default function MatchesPage() {
  const router = useRouter();
  const t = useTranslations('matches');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [replay, setReplay] = useState<MatchDetail | null>(null);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getMatches()
        .then((data) => setMatches(data.matches))
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  function resolveError(err: unknown): string {
    const code =
      err instanceof ApiError && tErrors.has(err.errorCode)
        ? err.errorCode
        : UNKNOWN_ERROR_CODE;
    return tErrors(code);
  }

  async function onSimulate(match: MatchSummary) {
    setActionError('');
    setBusyId(match.id);
    try {
      const detail = await simulateMatch(match.id);
      setMatches((prev) => prev.map((m) => (m.id === match.id ? toSummary(m, detail) : m)));
      setReplay(detail);
    } catch (err) {
      setActionError(resolveError(err));
    } finally {
      setBusyId(null);
    }
  }

  async function onReplay(match: MatchSummary) {
    setActionError('');
    setBusyId(match.id);
    try {
      setReplay(await getMatch(match.id));
    } catch (err) {
      setActionError(resolveError(err));
    } finally {
      setBusyId(null);
    }
  }

  if (isAuthenticated === null || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => router.replace('/team')}
            className="px-4 py-2 bg-accent text-surface font-semibold rounded-lg"
          >
            {t('backToTeam')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📅</span>
            <div>
              <h1 className="text-xl font-bold text-white">{t('title')}</h1>
              <p className="text-slate-400 text-sm">{t('subtitle')}</p>
            </div>
          </div>
          <button
            onClick={() => router.replace('/team')}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white border border-slate-600 hover:border-slate-500 rounded-lg transition-colors"
          >
            {t('backToTeam')}
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {actionError && (
          <p className="text-red-400 text-sm mb-4 text-center">{actionError}</p>
        )}
        {matches.length === 0 ? (
          <p className="text-slate-400 text-center py-12">{t('empty')}</p>
        ) : (
          <ul className="space-y-2">
            {matches.map((match) => (
              <MatchRow
                key={match.id}
                match={match}
                busy={busyId === match.id}
                onSimulate={() => onSimulate(match)}
                onReplay={() => onReplay(match)}
              />
            ))}
          </ul>
        )}
      </main>

      {replay && (
        <ReplayDialog detail={replay} onClose={() => setReplay(null)} />
      )}
    </div>
  );
}

function toSummary(previous: MatchSummary, detail: MatchDetail): MatchSummary {
  return {
    ...previous,
    played: detail.played,
    homeScore: detail.homeScore,
    awayScore: detail.awayScore,
  };
}

function MatchRow({
  match,
  busy,
  onSimulate,
  onReplay,
}: {
  match: MatchSummary;
  busy: boolean;
  onSimulate: () => void;
  onReplay: () => void;
}) {
  const t = useTranslations('matches');
  const myScore = match.isHome ? match.homeScore : match.awayScore;
  const oppScore = match.isHome ? match.awayScore : match.homeScore;

  return (
    <li className="bg-card border border-slate-700/50 rounded-xl px-4 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-xs font-mono text-slate-500 w-16 shrink-0">
          {t('round', { round: match.round })}
        </span>
        <span
          className={`inline-block px-2 py-0.5 rounded text-xs font-medium shrink-0 ${
            match.isHome
              ? 'bg-emerald-500/20 text-emerald-300'
              : 'bg-sky-500/20 text-sky-300'
          }`}
        >
          {match.isHome ? t('home') : t('away')}
        </span>
        <span className="font-medium text-white truncate">
          {match.opponentName}
        </span>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {match.played ? (
          <span className="font-mono font-bold text-white tabular-nums">
            {myScore}–{oppScore}
          </span>
        ) : (
          <span className="text-xs text-slate-500">{t('notPlayed')}</span>
        )}
        {match.played ? (
          <button
            onClick={onReplay}
            disabled={busy}
            className="text-xs font-medium text-accent border border-accent/40 hover:border-accent rounded px-3 py-1 transition-colors disabled:opacity-50"
          >
            {t('viewReplay')}
          </button>
        ) : (
          <button
            onClick={onSimulate}
            disabled={busy}
            className="text-xs font-semibold text-surface bg-accent hover:opacity-90 rounded px-3 py-1 transition-opacity disabled:opacity-50"
          >
            {busy ? t('simulating') : t('simulate')}
          </button>
        )}
      </div>
    </li>
  );
}

function ReplayDialog({
  detail,
  onClose,
}: {
  detail: MatchDetail;
  onClose: () => void;
}) {
  const t = useTranslations('matches');

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 bg-black/60 flex items-center justify-center px-4 z-20"
    >
      <div className="bg-card border border-slate-700 rounded-xl w-full max-w-lg shadow-2xl flex flex-col max-h-[85vh]">
        <div className="p-5 border-b border-slate-700/50">
          <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
            {t('replayTitle')}
          </p>
          <div className="flex items-center justify-center gap-4 text-white">
            <span className="font-medium flex-1 text-right truncate">
              {detail.homeTeamName}
            </span>
            <span className="font-mono font-bold text-2xl tabular-nums">
              {detail.homeScore}–{detail.awayScore}
            </span>
            <span className="font-medium flex-1 truncate">
              {detail.awayTeamName}
            </span>
          </div>
        </div>
        <div className="overflow-y-auto px-5 py-4">
          {detail.events.length === 0 ? (
            <p className="text-slate-400 text-center py-6">{t('noEvents')}</p>
          ) : (
            <ol className="space-y-1">
              {detail.events.map((event, index) => (
                <li
                  key={index}
                  className={`flex gap-3 text-sm py-1 ${
                    event.outcome === 'goal'
                      ? 'text-accent font-medium'
                      : 'text-slate-300'
                  }`}
                >
                  <span className="font-mono text-slate-500 w-8 shrink-0 text-right">
                    {event.minute}&apos;
                  </span>
                  <span>
                    {t(`outcomes.${event.outcome}`, { player: event.player })}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
        <div className="p-4 border-t border-slate-700/50">
          <button
            onClick={onClose}
            className="w-full py-2 text-sm font-medium text-slate-300 border border-slate-600 rounded-lg hover:text-white transition-colors"
          >
            {t('close')}
          </button>
        </div>
      </div>
    </div>
  );
}
