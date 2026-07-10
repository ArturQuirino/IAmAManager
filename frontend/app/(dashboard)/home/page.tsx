'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { getMatches, getStandings, MatchSummary } from '@/lib/api';
import { deriveHomeSummary, HomeSummary, resultKind } from '@/lib/home';
import { useAuth } from '@/hooks/useAuth';

export default function HomePage() {
  const t = useTranslations('home');
  const { isAuthenticated } = useAuth();
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      Promise.all([getMatches(), getStandings()])
        .then(([matches, standings]) =>
          setSummary(deriveHomeSummary(matches.matches, standings)),
        )
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  if (isAuthenticated === null || loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-4">
        <p className="text-red-400">{error || t('loadError')}</p>
      </div>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">{t('title')}</h1>
      <div className="grid gap-4 sm:grid-cols-2">
        <NextMatchCard match={summary.nextMatch} />
        <PositionCard summary={summary} />
      </div>
      <RecentResults results={summary.recentResults} />
    </main>
  );
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-card border border-slate-700/50 rounded-xl p-5 shadow-2xl">
      <p className="text-xs uppercase tracking-wide text-slate-500 mb-3">
        {title}
      </p>
      {children}
    </section>
  );
}

function NextMatchCard({ match }: { match: MatchSummary | null }) {
  const t = useTranslations('home');
  if (!match) {
    return (
      <Card title={t('nextMatch')}>
        <p className="text-slate-400">{t('noNextMatch')}</p>
      </Card>
    );
  }
  return (
    <Card title={t('nextMatch')}>
      <div className="flex items-center gap-3">
        <span
          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            match.isHome
              ? 'bg-emerald-500/20 text-emerald-300'
              : 'bg-sky-500/20 text-sky-300'
          }`}
        >
          {match.isHome ? t('home') : t('away')}
        </span>
        <span className="text-lg font-bold text-white truncate">
          {match.opponentName}
        </span>
      </div>
      <p className="text-slate-400 text-sm mt-2">
        {t('round', { round: match.round })}
      </p>
    </Card>
  );
}

function PositionCard({ summary }: { summary: HomeSummary }) {
  const t = useTranslations('home');
  return (
    <Card title={t('leaguePosition')}>
      {summary.position === null ? (
        <p className="text-slate-400">{t('noPosition')}</p>
      ) : (
        <>
          <p className="text-3xl font-bold text-white tabular-nums">
            {t('positionValue', {
              position: summary.position,
              total: summary.totalTeams,
            })}
          </p>
          {summary.divisionLevel !== null && (
            <p className="text-slate-400 text-sm mt-2">
              {t('divisionSeason', {
                level: summary.divisionLevel,
                season: summary.seasonNumber ?? 1,
              })}
            </p>
          )}
        </>
      )}
    </Card>
  );
}

function RecentResults({ results }: { results: MatchSummary[] }) {
  const t = useTranslations('home');
  return (
    <section className="mt-6">
      <p className="text-xs uppercase tracking-wide text-slate-500 mb-3">
        {t('recentResults')}
      </p>
      {results.length === 0 ? (
        <p className="text-slate-400">{t('noResults')}</p>
      ) : (
        <ul className="space-y-2">
          {results.map((match) => (
            <ResultRow key={match.id} match={match} />
          ))}
        </ul>
      )}
    </section>
  );
}

const RESULT_STYLES: Record<string, string> = {
  win: 'bg-emerald-500/20 text-emerald-300',
  draw: 'bg-slate-500/20 text-slate-300',
  loss: 'bg-red-500/20 text-red-300',
};

function ResultRow({ match }: { match: MatchSummary }) {
  const t = useTranslations('home');
  const kind = resultKind(match) ?? 'draw';
  const myScore = match.isHome ? match.homeScore : match.awayScore;
  const oppScore = match.isHome ? match.awayScore : match.homeScore;

  return (
    <li className="bg-card border border-slate-700/50 rounded-xl px-4 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <span
          className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold ${RESULT_STYLES[kind]}`}
        >
          {t(kind)}
        </span>
        <span className="font-medium text-white truncate">
          {match.opponentName}
        </span>
      </div>
      <span className="font-mono font-bold text-white tabular-nums shrink-0">
        {myScore}–{oppScore}
      </span>
    </li>
  );
}
