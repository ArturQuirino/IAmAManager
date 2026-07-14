'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import {
  ApiError,
  getTeamInfo,
  TeamInfo,
  updateTeamName,
  UNKNOWN_ERROR_CODE,
} from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

const TEAM_NAME_MIN_LENGTH = 2;
const TEAM_NAME_MAX_LENGTH = 50;

// Season record fields, in display order. Each maps to a `TeamInfo` numeric
// field and a label under the `team.stats` namespace.
const RECORD_FIELDS = [
  'played',
  'wins',
  'draws',
  'losses',
  'goalsFor',
  'goalsAgainst',
  'goalDifference',
  'points',
] as const;

export default function TeamPage() {
  const t = useTranslations('team');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getTeamInfo()
        .then((data) => {
          setTeam(data);
          setName(data.teamName);
        })
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaveError('');
    setSaved(false);
    setSaving(true);
    try {
      const updated = await updateTeamName(name);
      setTeam(updated);
      setName(updated.teamName);
      setSaved(true);
    } catch (err) {
      const code =
        err instanceof ApiError && tErrors.has(err.errorCode)
          ? err.errorCode
          : UNKNOWN_ERROR_CODE;
      setSaveError(tErrors(code));
    } finally {
      setSaving(false);
    }
  }

  if (isAuthenticated === null || loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <p className="text-red-400">{error || t('loadError')}</p>
      </div>
    );
  }

  const trimmedName = name.trim();
  const isUnchanged = trimmedName === team.teamName;
  const isTooShort = trimmedName.length < TEAM_NAME_MIN_LENGTH;

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">⚽</span>
        <div>
          <h1 className="text-2xl font-bold text-white">{t('title')}</h1>
          <p className="text-slate-400 text-sm">{t('subtitle')}</p>
        </div>
      </div>

      <section className="bg-card border border-slate-700/50 rounded-xl p-6 shadow-2xl mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="teamName"
              className="block text-sm font-medium text-slate-300 mb-1.5"
            >
              {t('nameLabel')}
            </label>
            <input
              id="teamName"
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setSaved(false);
                setSaveError('');
              }}
              required
              minLength={TEAM_NAME_MIN_LENGTH}
              maxLength={TEAM_NAME_MAX_LENGTH}
              autoComplete="off"
              className="w-full px-4 py-2.5 bg-surface border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent transition"
            />
          </div>

          {saveError && (
            <p className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2.5">
              {saveError}
            </p>
          )}

          {saved && (
            <p className="text-accent text-sm bg-accent/10 border border-accent/20 rounded-lg px-4 py-2.5">
              {t('saved')}
            </p>
          )}

          <button
            type="submit"
            disabled={saving || isUnchanged || isTooShort}
            className="w-full py-2.5 px-4 bg-accent hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-surface font-semibold rounded-lg transition-colors"
          >
            {saving ? t('saving') : t('save')}
          </button>
        </form>
      </section>

      <section className="bg-card border border-slate-700/50 rounded-xl p-6 shadow-2xl">
        <p className="text-xs uppercase tracking-wide text-slate-500 mb-4">
          {t('overview')}
        </p>

        <dl className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <dt className="text-slate-400 text-sm">{t('division')}</dt>
            <dd className="text-white font-semibold">
              {team.divisionLevel === null
                ? t('noDivision')
                : t('divisionSeason', {
                    level: team.divisionLevel,
                    season: team.seasonNumber ?? 1,
                  })}
            </dd>
          </div>
          <div>
            <dt className="text-slate-400 text-sm">{t('players')}</dt>
            <dd className="text-white font-semibold">{team.playersCount}</dd>
          </div>
        </dl>

        <dl className="grid grid-cols-4 gap-3 text-center">
          {RECORD_FIELDS.map((field) => (
            <div
              key={field}
              className="bg-surface/50 border border-slate-700/50 rounded-lg py-3"
            >
              <dt className="text-xs uppercase tracking-wide text-slate-500">
                {t(`stats.${field}`)}
              </dt>
              <dd className="text-lg font-bold text-white font-mono tabular-nums">
                {team[field]}
              </dd>
            </div>
          ))}
        </dl>
      </section>
    </main>
  );
}
