'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  addYouthPlayer,
  ApiError,
  getYouth,
  UNKNOWN_ERROR_CODE,
  YouthCandidate,
} from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

const ATTRIBUTES = [
  'pace',
  'shooting',
  'passing',
  'dribbling',
  'defending',
  'physical',
] as const;

export default function YouthPage() {
  const router = useRouter();
  const t = useTranslations('youth');
  const tTeam = useTranslations('team');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [candidates, setCandidates] = useState<YouthCandidate[]>([]);
  const [squadSize, setSquadSize] = useState(0);
  const [maxSquadSize, setMaxSquadSize] = useState(40);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [addingId, setAddingId] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getYouth()
        .then((data) => {
          setCandidates(data.candidates);
          setSquadSize(data.squadSize);
          setMaxSquadSize(data.maxSquadSize);
        })
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  const isFull = squadSize >= maxSquadSize;

  async function handleAdd(candidateId: string) {
    setActionError('');
    setAddingId(candidateId);
    try {
      const data = await addYouthPlayer(candidateId);
      setCandidates(data.candidates);
      setSquadSize(data.squadSize);
      setMaxSquadSize(data.maxSquadSize);
    } catch (err) {
      const code =
        err instanceof ApiError && tErrors.has(err.errorCode)
          ? err.errorCode
          : UNKNOWN_ERROR_CODE;
      setActionError(tErrors(code));
    } finally {
      setAddingId(null);
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
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🌱</span>
            <div>
              <h1 className="text-xl font-bold text-white">{t('title')}</h1>
              <p className="text-slate-400 text-sm">
                {t('subtitle')} ·{' '}
                {t('squadCount', { size: squadSize, max: maxSquadSize })}
              </p>
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

      <main className="max-w-4xl mx-auto px-4 py-8">
        {isFull && (
          <p className="mb-6 text-amber-400 text-sm bg-amber-400/10 border border-amber-400/20 rounded-lg px-4 py-2.5">
            {t('fullNotice')}
          </p>
        )}
        {actionError && (
          <p className="mb-6 text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2.5">
            {actionError}
          </p>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          {candidates.map((candidate) => (
            <div
              key={candidate.id}
              className="bg-card border border-slate-700/50 rounded-xl p-5 shadow-lg"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {candidate.name}
                  </h2>
                  <span className="inline-block mt-1 px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs font-medium">
                    {tTeam(`positions.${candidate.position}`)}
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">{t('overall')}</p>
                  <p className="text-2xl font-bold text-accent">
                    {candidate.overall}
                  </p>
                </div>
              </div>
              <dl className="grid grid-cols-3 gap-2 mb-4">
                {ATTRIBUTES.map((key) => (
                  <div key={key} className="text-center">
                    <dt className="text-slate-500 text-[10px] uppercase tracking-wide">
                      {tTeam(`columns.${key}`)}
                    </dt>
                    <dd className="text-white font-mono text-sm">
                      {candidate[key]}
                    </dd>
                  </div>
                ))}
              </dl>
              <button
                onClick={() => handleAdd(candidate.id)}
                disabled={isFull || addingId !== null}
                className="w-full py-2 text-sm font-semibold text-surface bg-accent hover:bg-green-500 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {addingId === candidate.id ? t('adding') : t('add')}
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
