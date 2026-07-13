'use client';

import type { DragEvent } from 'react';
import { useTranslations } from 'next-intl';
import type { Player } from '@/lib/api';

interface PlayerChipProps {
  player: Player;
  isDragging: boolean;
  variant: 'pitch' | 'bench';
  onDragStart: (playerId: string) => void;
  onDragEnd: () => void;
}

export default function PlayerChip({
  player,
  isDragging,
  variant,
  onDragStart,
  onDragEnd,
}: PlayerChipProps) {
  const tTeam = useTranslations('team');

  function handleDragStart(event: DragEvent<HTMLDivElement>) {
    // Firefox needs data set for the drag to start; the actual id travels
    // through React state because Chrome hides the data until drop.
    event.dataTransfer.setData('text/plain', player.id);
    event.dataTransfer.effectAllowed = 'move';
    onDragStart(player.id);
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      aria-label={player.name}
      className={`flex flex-col items-center w-16 cursor-grab select-none ${
        isDragging ? 'opacity-40' : ''
      }`}
    >
      <div
        className={`w-12 h-9 flex items-center justify-center rounded border text-[10px] font-bold shadow-md ${
          player.position === 'GK'
            ? 'bg-amber-400 border-amber-300 text-slate-900'
            : variant === 'pitch'
              ? 'bg-card border-slate-500 text-slate-100'
              : 'bg-slate-700 border-slate-600 text-slate-200'
        }`}
      >
        {tTeam(`positions.${player.position}`)}
      </div>
      <span
        className={`mt-1 max-w-full truncate text-center text-xs font-medium ${
          variant === 'pitch' ? 'text-white drop-shadow' : 'text-slate-200'
        }`}
      >
        {player.name}
      </span>
    </div>
  );
}
