'use client';

import type { DragEvent } from 'react';
import { useTranslations } from 'next-intl';
import type { Player } from '@/lib/api';
import PlayerChip from '@/components/tactics/PlayerChip';

interface BenchListProps {
  players: Player[];
  draggingId: string | null;
  isDropActive: boolean;
  onDropToBench: (playerId: string) => void;
  onDragStart: (playerId: string) => void;
  onDragEnd: () => void;
}

export default function BenchList({
  players,
  draggingId,
  isDropActive,
  onDropToBench,
  onDragStart,
  onDragEnd,
}: BenchListProps) {
  const t = useTranslations('tactics');

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const playerId = draggingId ?? event.dataTransfer.getData('text/plain');
    if (playerId) onDropToBench(playerId);
  }

  return (
    <div
      role="region"
      aria-label={t('bench')}
      onDrop={handleDrop}
      onDragOver={(event) => event.preventDefault()}
      className={`bg-card border rounded-xl p-4 shadow-lg transition-colors ${
        isDropActive ? 'border-accent/60 bg-accent/5' : 'border-slate-700/50'
      }`}
    >
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">
        {t('bench')}
      </h2>
      {players.length === 0 ? (
        <p className="text-sm text-slate-500">
          {isDropActive ? t('benchDropHint') : t('benchEmpty')}
        </p>
      ) : (
        <div className="flex flex-wrap gap-3">
          {players.map((player) => (
            <PlayerChip
              key={player.id}
              player={player}
              isDragging={draggingId === player.id}
              variant="bench"
              onDragStart={onDragStart}
              onDragEnd={onDragEnd}
            />
          ))}
        </div>
      )}
    </div>
  );
}
