'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  ApiError,
  getTactics,
  Player,
  PlayerPosition,
  setStartingXi,
  UNKNOWN_ERROR_CODE,
} from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

const REQUIRED_STARTERS = 11;

// Outfield lines, in the order a formation string reads (e.g. "4-3-3").
const FORMATION_LINES: PlayerPosition[] = ['DEF', 'MID', 'ATT'];

const POSITION_ORDER: Record<PlayerPosition, number> = {
  GK: 0,
  DEF: 1,
  MID: 2,
  ATT: 3,
};

function byPosition(a: Player, b: Player): number {
  return (
    POSITION_ORDER[a.position] - POSITION_ORDER[b.position] ||
    a.name.localeCompare(b.name)
  );
}

// Mirrors the backend: the shape is read off the selected outfield players,
// null while nothing is selected so the UI can show a placeholder.
function deriveFormation(selected: Player[]): string | null {
  const outfield = selected.filter((player) => player.position !== 'GK');
  if (outfield.length === 0) return null;
  return FORMATION_LINES.map(
    (line) => outfield.filter((player) => player.position === line).length,
  ).join('-');
}

export default function TacticsPage() {
  const router = useRouter();
  const t = useTranslations('tactics');
  const tTeam = useTranslations('team');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [squad, setSquad] = useState<Player[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getTactics()
        .then((data) => {
          setSquad([...data.starters, ...data.bench].sort(byPosition));
          setSelectedIds(new Set(data.starters.map((player) => player.id)));
        })
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  const selectedPlayers = useMemo(
    () => squad.filter((player) => selectedIds.has(player.id)),
    [squad, selectedIds],
  );
  const goalkeeperCount = selectedPlayers.filter(
    (player) => player.position === 'GK',
  ).length;
  const isValid =
    selectedIds.size === REQUIRED_STARTERS && goalkeeperCount === 1;
  const formation = deriveFormation(selectedPlayers);

  function toggle(playerId: string) {
    setSaved(false);
    setActionError('');
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(playerId)) next.delete(playerId);
      else next.add(playerId);
      return next;
    });
  }

  async function handleSave() {
    setActionError('');
    setSaved(false);
    setSaving(true);
    try {
      const data = await setStartingXi(Array.from(selectedIds));
      setSquad([...data.starters, ...data.bench].sort(byPosition));
      setSelectedIds(new Set(data.starters.map((player) => player.id)));
      setSaved(true);
    } catch (err) {
      const code =
        err instanceof ApiError && tErrors.has(err.errorCode)
          ? err.errorCode
          : UNKNOWN_ERROR_CODE;
      setActionError(tErrors(code));
    } finally {
      setSaving(false);
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
            <span className="text-2xl">📋</span>
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

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-card border border-slate-700/50 rounded-xl p-5 mb-6 shadow-lg flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {t('selected')}
            </p>
            <p
              className={`text-lg font-bold font-mono ${
                selectedIds.size === REQUIRED_STARTERS
                  ? 'text-accent'
                  : 'text-white'
              }`}
            >
              {t('selectedCount', { count: selectedIds.size })}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {tTeam('positions.GK')}
            </p>
            <p
              className={`text-lg font-bold font-mono ${
                goalkeeperCount === 1 ? 'text-accent' : 'text-white'
              }`}
            >
              {goalkeeperCount}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {t('formation')}
            </p>
            <p className="text-lg font-bold font-mono text-white">
              {formation ?? t('formationEmpty')}
            </p>
          </div>
          <div className="ml-auto text-right">
            <button
              onClick={handleSave}
              disabled={!isValid || saving}
              className="px-5 py-2 text-sm font-semibold text-surface bg-accent hover:bg-green-500 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? t('saving') : t('save')}
            </button>
          </div>
        </div>

        <p className="mb-4 text-sm text-slate-400">{t('requirements')}</p>
        {saved && (
          <p className="mb-4 text-accent text-sm bg-accent/10 border border-accent/20 rounded-lg px-4 py-2.5">
            {t('saved')}
          </p>
        )}
        {actionError && (
          <p className="mb-4 text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2.5">
            {actionError}
          </p>
        )}

        <div className="bg-card border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50 bg-surface/50">
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-16">
                    {t('inXi')}
                  </th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium">
                    {tTeam('columns.name')}
                  </th>
                  <th className="px-4 py-3 text-left text-slate-400 font-medium w-20">
                    {tTeam('columns.position')}
                  </th>
                  <th className="px-4 py-3 text-right text-slate-400 font-medium w-20">
                    {tTeam('columns.overall')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {squad.map((player, index) => {
                  const isSelected = selectedIds.has(player.id);
                  return (
                    <tr
                      key={player.id}
                      className={`border-b border-slate-700/30 ${
                        isSelected
                          ? 'bg-accent/10'
                          : index % 2 === 0
                            ? 'bg-transparent'
                            : 'bg-surface/30'
                      } hover:bg-accent/5 transition-colors`}
                    >
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggle(player.id)}
                          aria-label={player.name}
                          className="w-4 h-4 accent-accent cursor-pointer"
                        />
                      </td>
                      <td className="px-4 py-3 font-medium text-white">
                        {player.name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-xs font-medium">
                          {tTeam(`positions.${player.position}`)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-white font-mono">
                        {player.overall}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
