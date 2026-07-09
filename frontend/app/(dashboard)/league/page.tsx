'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { getStandings, StandingsResponse } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

// A division promotes its top two and relegates its bottom two (see
// docs/competition.md). Used only to tint the zone rows.
const PROMOTION_SLOTS = 2;
const RELEGATION_SLOTS = 2;

export default function LeaguePage() {
  const router = useRouter();
  const t = useTranslations('league');
  const { isAuthenticated } = useAuth();
  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated === false) return;

    if (isAuthenticated) {
      getStandings()
        .then((data) => setStandings(data))
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

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

  const entries = standings?.entries ?? [];
  const hasZones = entries.length > PROMOTION_SLOTS + RELEGATION_SLOTS;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏆</span>
            <div>
              <h1 className="text-xl font-bold text-white">{t('title')}</h1>
              {standings?.divisionLevel != null && (
                <p className="text-slate-400 text-sm">
                  {t('subtitle', {
                    level: standings.divisionLevel,
                    season: standings.seasonNumber ?? 1,
                  })}
                </p>
              )}
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
        {entries.length === 0 ? (
          <p className="text-slate-400 text-center py-12">{t('empty')}</p>
        ) : (
          <div className="bg-card border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50 bg-surface/50">
                    <th className="px-3 py-3 text-right text-slate-400 font-medium w-10">
                      {t('columns.position')}
                    </th>
                    <th className="px-4 py-3 text-left text-slate-400 font-medium">
                      {t('columns.team')}
                    </th>
                    {(
                      [
                        'played',
                        'wins',
                        'draws',
                        'losses',
                        'goalsFor',
                        'goalsAgainst',
                        'goalDifference',
                        'points',
                      ] as const
                    ).map((column) => (
                      <th
                        key={column}
                        className="px-3 py-3 text-right text-slate-400 font-medium w-12"
                      >
                        {t(`columns.${column}`)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry, index) => {
                    const isPromotion = hasZones && index < PROMOTION_SLOTS;
                    const isRelegation =
                      hasZones && index >= entries.length - RELEGATION_SLOTS;
                    return (
                      <tr
                        key={entry.teamId}
                        className={`border-b border-slate-700/30 transition-colors ${
                          entry.isCurrentUserTeam
                            ? 'bg-accent/10'
                            : 'hover:bg-accent/5'
                        }`}
                      >
                        <td className="px-3 py-3 text-right text-slate-400 font-mono">
                          <span className="inline-flex items-center gap-1 justify-end">
                            {isPromotion && (
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full bg-green-400"
                                title={t('zones.promotion')}
                              />
                            )}
                            {isRelegation && (
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full bg-red-400"
                                title={t('zones.relegation')}
                              />
                            )}
                            {index + 1}
                          </span>
                        </td>
                        <td
                          className={`px-4 py-3 font-medium ${
                            entry.isCurrentUserTeam
                              ? 'text-accent'
                              : 'text-white'
                          }`}
                        >
                          {entry.teamName}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.played}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.wins}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.draws}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.losses}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.goalsFor}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.goalsAgainst}
                        </td>
                        <td className="px-3 py-3 text-right text-slate-300 font-mono">
                          {entry.goalDifference}
                        </td>
                        <td className="px-3 py-3 text-right font-bold text-white font-mono">
                          {entry.points}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
