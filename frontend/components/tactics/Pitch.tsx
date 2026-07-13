'use client';

import type { DragEvent } from 'react';
import { useTranslations } from 'next-intl';
import type { Player } from '@/lib/api';
import {
  LINE_BANDS,
  lineY,
  playerX,
  resolveDrop,
  type DropTarget,
  type LineId,
  type PitchState,
} from '@/lib/tactics';
import PlayerChip from '@/components/tactics/PlayerChip';

interface PitchProps {
  pitch: PitchState;
  playersById: Map<string, Player>;
  draggingId: string | null;
  onDropPlayer: (playerId: string, target: DropTarget | null) => void;
  onDragStart: (playerId: string) => void;
  onDragEnd: () => void;
}

const LINE_LABELS: Record<LineId, 'ATT' | 'MID' | 'DEF' | 'GK'> = {
  att: 'ATT',
  mid: 'MID',
  def: 'DEF',
  goal: 'GK',
};

export default function Pitch({
  pitch,
  playersById,
  draggingId,
  onDropPlayer,
  onDragStart,
  onDragEnd,
}: PitchProps) {
  const t = useTranslations('tactics');
  const tTeam = useTranslations('team');

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const playerId = draggingId ?? event.dataTransfer.getData('text/plain');
    const player = playerId ? playersById.get(playerId) : undefined;
    if (!player) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const y = (event.clientY - rect.top) / rect.height;
    onDropPlayer(
      player.id,
      resolveDrop({ x, y, playerPosition: player.position, pitch, draggingId }),
    );
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }

  return (
    <div
      role="region"
      aria-label={t('pitch')}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="relative w-full aspect-[4/5] rounded-xl border-2 border-white/30 bg-gradient-to-b from-green-700 to-green-900 shadow-2xl"
    >
      {/* Band separators */}
      {LINE_BANDS.filter(({ from }) => from > 0).map(({ line, from }) => (
        <div
          key={line}
          aria-hidden
          className="absolute inset-x-0 border-t border-dashed border-white/25"
          style={{ top: `${from * 100}%` }}
        />
      ))}

      {/* Line labels */}
      {LINE_BANDS.map(({ line }) => (
        <span
          key={line}
          aria-hidden
          className="absolute left-2 -translate-y-1/2 text-[10px] font-bold uppercase tracking-widest text-white/40"
          style={{ top: `${lineY(line) * 100}%` }}
        >
          {tTeam(`positions.${LINE_LABELS[line]}`)}
        </span>
      ))}

      {/* Penalty box and goal frame at the bottom */}
      <div
        aria-hidden
        className="absolute bottom-0 left-1/2 h-[13%] w-1/2 -translate-x-1/2 border-2 border-b-0 border-white/30"
      />
      <div
        aria-hidden
        className="absolute bottom-0 left-1/2 h-2 w-1/5 -translate-x-1/2 rounded-t-sm bg-white/50"
      />

      {/* Players, centered per line by count */}
      {LINE_BANDS.flatMap(({ line }) =>
        pitch[line].map((playerId, index) => {
          const player = playersById.get(playerId);
          if (!player) return null;
          return (
            <div
              key={playerId}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{
                left: `${playerX(index, pitch[line].length) * 100}%`,
                top: `${lineY(line) * 100}%`,
              }}
            >
              <PlayerChip
                player={player}
                isDragging={draggingId === player.id}
                variant="pitch"
                onDragStart={onDragStart}
                onDragEnd={onDragEnd}
              />
            </div>
          );
        }),
      )}
    </div>
  );
}
