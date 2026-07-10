'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  ApiError,
  getSquad,
  Player,
  removePlayer,
  UNKNOWN_ERROR_CODE,
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

export default function SquadPage() {
  const router = useRouter();
  const t = useTranslations('squad');
  const tTeam = useTranslations('team');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [teamName, setTeamName] = useState('');
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [pendingRemoval, setPendingRemoval] = useState<Player | null>(null);
  const [actionError, setActionError] = useState('');
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getSquad()
        .then((data) => {
          setTeamName(data.teamName);
          setPlayers(data.players);
        })
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  async function confirmRemoval() {
    if (!pendingRemoval) return;
    setActionError('');
    setRemoving(true);
    try {
      const data = await removePlayer(pendingRemoval.id);
      setPlayers(data.players);
      setPendingRemoval(null);
    } catch (err) {
      const code =
        err instanceof ApiError && tErrors.has(err.errorCode)
          ? err.errorCode
          : UNKNOWN_ERROR_CODE;
      setActionError(tErrors(code));
    } finally {
      setRemoving(false);
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
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👥</span>
            <div>
              <h1 className="text-xl font-bold text-white">{t('title')}</h1>
              <p className="text-slate-400 text-sm">
                {teamName} · {t('playersCount', { count: players.length })}
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

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="bg-card border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 bg-surface/50">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">
                    {tTeam('columns.name')}
                  </th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-20">
                    {tTeam('columns.position')}
                  </th>
                  {ATTRIBUTES.map((key) => (
                    <th
                      key={key}
                      className="px-3 py-3 text-right text-slate-400 font-medium w-16"
                    >
                      {tTeam(`columns.${key}`)}
                    </th>
                  ))}
                  <th className="px-4 py-3 text-right text-slate-400 font-medium w-20">
                    {tTeam('columns.overall')}
                  </th>
                  <th className="px-4 py-3 w-24" />
                </tr>
              </thead>
              <tbody>
                {players.map((player, index) => (
                  <tr
                    key={player.id}
                    className={`border-b border-slate-700/30 ${
                      index % 2 === 0 ? 'bg-transparent' : 'bg-surface/30'
                    } hover:bg-accent/5 transition-colors`}
                  >
                    <td className="px-4 py-3 font-medium text-white">
                      {player.name}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-block px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs font-medium">
                        {tTeam(`positions.${player.position}`)}
                      </span>
                    </td>
                    {ATTRIBUTES.map((key) => (
                      <td
                        key={key}
                        className="px-3 py-3 text-right text-slate-300 font-mono"
                      >
                        {player[key]}
                      </td>
                    ))}
                    <td className="px-4 py-3 text-right font-bold text-white font-mono">
                      {player.overall}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          setActionError('');
                          setPendingRemoval(player);
                        }}
                        className="text-xs font-medium text-red-400 hover:text-red-300 border border-red-400/30 hover:border-red-300/50 rounded px-3 py-1 transition-colors"
                      >
                        {t('release')}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {pendingRemoval && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 bg-black/60 flex items-center justify-center px-4 z-20"
        >
          <div className="bg-card border border-slate-700 rounded-xl p-6 max-w-sm w-full shadow-2xl">
            <p className="text-white mb-4">
              {t('releaseConfirm', { name: pendingRemoval.name })}
            </p>
            {actionError && (
              <p className="text-red-400 text-sm mb-4">{actionError}</p>
            )}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setPendingRemoval(null)}
                disabled={removing}
                className="px-4 py-2 text-sm font-medium text-slate-300 border border-slate-600 rounded-lg disabled:opacity-50"
              >
                {t('cancel')}
              </button>
              <button
                onClick={confirmRemoval}
                disabled={removing}
                className="px-4 py-2 text-sm font-semibold text-white bg-red-500 hover:bg-red-600 rounded-lg disabled:opacity-50"
              >
                {t('confirmRelease')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
