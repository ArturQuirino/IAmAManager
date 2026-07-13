'use client';

import { useState, type DragEvent } from 'react';
import { useTranslations } from 'next-intl';
import type { Player } from '@/lib/api';

interface PlayerChipProps {
  player: Player;
  isDragging: boolean;
  variant: 'pitch' | 'bench';
  onDragStart: (playerId: string) => void;
  onDragEnd: () => void;
}

const ATTRIBUTES = [
  'pace',
  'shooting',
  'passing',
  'dribbling',
  'defending',
  'physical',
] as const;

export default function PlayerChip({
  player,
  isDragging,
  variant,
  onDragStart,
  onDragEnd,
}: PlayerChipProps) {
  const tTeam = useTranslations('team');
  const [isHovered, setIsHovered] = useState(false);

  function handleDragStart(event: DragEvent<HTMLDivElement>) {
    // Firefox needs data set for the drag to start; the actual id travels
    // through React state because Chrome hides the data until drop.
    event.dataTransfer.setData('text/plain', player.id);
    event.dataTransfer.effectAllowed = 'move';
    setIsHovered(false);
    onDragStart(player.id);
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      aria-label={player.name}
      className={`relative flex flex-col items-center w-16 cursor-grab select-none ${
        isHovered && !isDragging ? 'z-50' : ''
      } ${isDragging ? 'opacity-40' : ''}`}
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

      {isHovered && !isDragging && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 pointer-events-none w-40 rounded-lg border border-slate-600 bg-slate-900 p-3 shadow-2xl"
        >
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className="text-xs font-semibold text-white truncate">
              {player.name}
            </span>
            <span className="text-sm font-bold text-accent font-mono">
              {player.overall}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1">
            {ATTRIBUTES.map((key) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-[10px] uppercase text-slate-400">
                  {tTeam(`columns.${key}`)}
                </span>
                <span className="text-xs font-mono text-slate-200">
                  {player[key]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
