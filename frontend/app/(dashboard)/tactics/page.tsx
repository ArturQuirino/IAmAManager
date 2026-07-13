'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import {
  ApiError,
  getTactics,
  Player,
  setStartingXi,
  UNKNOWN_ERROR_CODE,
} from '@/lib/api';
import {
  applyDrop,
  autoArrange,
  createEmptyPitch,
  deriveFormation,
  findLineOf,
  isValidXi,
  placedIds,
  removeFromPitch,
  REQUIRED_STARTERS,
  type DropTarget,
  type PitchState,
} from '@/lib/tactics';
import { useAuth } from '@/hooks/useAuth';
import Pitch from '@/components/tactics/Pitch';
import BenchList from '@/components/tactics/BenchList';

// Delay between the last pitch change and the auto-save request, so a burst of
// drags results in a single write rather than one per intermediate state.
const AUTOSAVE_DEBOUNCE_MS = 500;

export default function TacticsPage() {
  const router = useRouter();
  const t = useTranslations('tactics');
  const tTeam = useTranslations('team');
  const tErrors = useTranslations('errors');
  const { isAuthenticated } = useAuth();
  const [squad, setSquad] = useState<Player[]>([]);
  const [pitch, setPitch] = useState<PitchState>(createEmptyPitch);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [isInvalidDrop, setIsInvalidDrop] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>(
    'idle',
  );
  // The first pitch state after load is the already-persisted XI, so it must
  // not trigger an auto-save; this flips once that initial state has settled.
  const hasLoaded = useRef(false);
  // Identifies the latest in-flight save so stale responses are ignored.
  const saveSeq = useRef(0);

  useEffect(() => {
    if (isAuthenticated === false) return;
    if (isAuthenticated) {
      getTactics()
        .then((data) => {
          setSquad([...data.starters, ...data.bench]);
          setPitch(autoArrange(data.starters));
        })
        .catch(() => setError(t('loadError')))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated, t]);

  const playersById = useMemo(
    () => new Map(squad.map((player) => [player.id, player])),
    [squad],
  );
  const placed = placedIds(pitch);
  const bench = useMemo(() => {
    const onPitch = new Set(placedIds(pitch));
    return squad.filter((player) => !onPitch.has(player.id));
  }, [squad, pitch]);
  const goalkeeperCount = pitch.goal[0] === null ? 0 : 1;
  const formation = deriveFormation(pitch);
  const isDraggingFromPitch =
    draggingId !== null && findLineOf(pitch, draggingId) !== null;
  const actionError = errorCode
    ? tErrors(tErrors.has(errorCode) ? errorCode : UNKNOWN_ERROR_CODE)
    : '';

  // Auto-save: whenever the pitch reaches a valid XI, persist it after a short
  // debounce so rapid drags collapse into one request. The response is not
  // applied back to the pitch (the backend stores only who starts, not their
  // on-pitch arrangement), which keeps the user's manual layout intact.
  useEffect(() => {
    if (loading) return;
    if (!hasLoaded.current) {
      hasLoaded.current = true;
      return;
    }
    if (!isValidXi(pitch)) return;

    const ids = placedIds(pitch);
    const seq = (saveSeq.current += 1);
    setErrorCode(null);
    setSaveState('saving');
    const timer = setTimeout(() => {
      setStartingXi(ids)
        .then(() => {
          if (seq === saveSeq.current) setSaveState('saved');
        })
        .catch((err) => {
          if (seq !== saveSeq.current) return;
          setErrorCode(err instanceof ApiError ? err.errorCode : UNKNOWN_ERROR_CODE);
          setSaveState('idle');
        });
    }, AUTOSAVE_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [pitch, loading]);

  function handleDragStart(playerId: string) {
    setDraggingId(playerId);
    setIsInvalidDrop(false);
    setErrorCode(null);
  }

  function handleDropPlayer(playerId: string, target: DropTarget | null) {
    setDraggingId(null);
    if (target === null) {
      setIsInvalidDrop(true);
      return;
    }
    setIsInvalidDrop(false);
    setPitch((prev) => applyDrop(prev, playerId, target));
  }

  function handleDropToBench(playerId: string) {
    setDraggingId(null);
    setIsInvalidDrop(false);
    setPitch((prev) => removeFromPitch(prev, playerId));
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

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="bg-card border border-slate-700/50 rounded-xl p-5 mb-6 shadow-lg flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              {t('selected')}
            </p>
            <p
              className={`text-lg font-bold font-mono ${
                placed.length === REQUIRED_STARTERS
                  ? 'text-accent'
                  : 'text-white'
              }`}
            >
              {t('selectedCount', { count: placed.length })}
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
          <div className="ml-auto text-right min-h-[1.5rem] flex items-center justify-end">
            {saveState === 'saving' && (
              <span className="flex items-center gap-2 text-sm text-slate-400">
                <span className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                {t('saving')}
              </span>
            )}
            {saveState === 'saved' && (
              <span className="flex items-center gap-1.5 text-sm text-accent">
                <span aria-hidden="true">✓</span>
                {t('saved')}
              </span>
            )}
          </div>
        </div>

        <p className="mb-2 text-sm text-slate-400">{t('requirements')}</p>
        <p className="mb-4 text-sm text-slate-500">{t('dragHint')}</p>
        {actionError && (
          <p className="mb-4 text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2.5">
            {actionError}
          </p>
        )}
        {isInvalidDrop && (
          <p className="mb-4 text-amber-400 text-sm bg-amber-400/10 border border-amber-400/20 rounded-lg px-4 py-2.5">
            {t('invalidDrop')}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] items-start">
          <Pitch
            pitch={pitch}
            playersById={playersById}
            draggingId={draggingId}
            onDropPlayer={handleDropPlayer}
            onDragStart={handleDragStart}
            onDragEnd={() => setDraggingId(null)}
          />
          <BenchList
            players={bench}
            draggingId={draggingId}
            isDropActive={isDraggingFromPitch}
            onDropToBench={handleDropToBench}
            onDragStart={handleDragStart}
            onDragEnd={() => setDraggingId(null)}
          />
        </div>
      </main>
    </div>
  );
}
