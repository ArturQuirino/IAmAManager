import type { Player, PlayerPosition } from '@/lib/api';

export type LineId = 'goal' | 'def' | 'mid' | 'att';

// Slot arrays hold player ids; null marks an empty slot.
export type PitchState = Record<LineId, (string | null)[]>;

export interface DropTarget {
  line: LineId;
  slot: number;
}

export const REQUIRED_STARTERS = 11;

export const LINE_SLOT_COUNTS: Record<LineId, number> = {
  goal: 1,
  def: 5,
  mid: 5,
  att: 5,
};

// Vertical bands of the pitch, top to bottom (attack at the top, own goal at
// the bottom). Fractions of the pitch height; the bands partition [0, 1].
export const LINE_BANDS: { line: LineId; from: number; to: number }[] = [
  { line: 'att', from: 0, to: 0.3 },
  { line: 'mid', from: 0.3, to: 0.58 },
  { line: 'def', from: 0.58, to: 0.84 },
  { line: 'goal', from: 0.84, to: 1 },
];

// A drop lands "directly on" an occupied slot (replace/swap) when it is
// within this fraction of the slot's width from the slot center.
const DIRECT_HIT_FRACTION = 0.3;

// Order a formation string reads (e.g. "4-3-3").
const FORMATION_LINES: LineId[] = ['def', 'mid', 'att'];

// Preferred line per outfield position, then where overflow spills to.
const POSITION_LINES: Record<Exclude<PlayerPosition, 'GK'>, LineId[]> = {
  DEF: ['def', 'mid', 'att'],
  MID: ['mid', 'def', 'att'],
  ATT: ['att', 'mid', 'def'],
};

export function createEmptyPitch(): PitchState {
  return {
    goal: Array<string | null>(LINE_SLOT_COUNTS.goal).fill(null),
    def: Array<string | null>(LINE_SLOT_COUNTS.def).fill(null),
    mid: Array<string | null>(LINE_SLOT_COUNTS.mid).fill(null),
    att: Array<string | null>(LINE_SLOT_COUNTS.att).fill(null),
  };
}

// Horizontal center of a slot, as a fraction of the pitch width.
export function slotX(line: LineId, slot: number): number {
  return (slot + 0.5) / LINE_SLOT_COUNTS[line];
}

// Vertical center of a line's band, as a fraction of the pitch height.
export function lineY(line: LineId): number {
  const band = LINE_BANDS.find((candidate) => candidate.line === line);
  if (!band) throw new Error(`Unknown line: ${line}`);
  return (band.from + band.to) / 2;
}

function lineAt(y: number): LineId {
  const band = LINE_BANDS.find(
    (candidate) => y >= candidate.from && y < candidate.to,
  );
  return band ? band.line : 'goal';
}

export function findSlot(
  pitch: PitchState,
  playerId: string,
): DropTarget | null {
  for (const { line } of LINE_BANDS) {
    const slot = pitch[line].indexOf(playerId);
    if (slot !== -1) return { line, slot };
  }
  return null;
}

// Resolves a drop at normalized coordinates (x, y in [0, 1]) to a slot, or
// null when the drop is not allowed: only goalkeepers may target the goal
// band, and goalkeepers may target nothing else.
export function resolveDrop(args: {
  x: number;
  y: number;
  playerPosition: PlayerPosition;
  pitch: PitchState;
}): DropTarget | null {
  const { x, y, playerPosition, pitch } = args;
  const line = lineAt(y);
  const isKeeper = playerPosition === 'GK';
  if (isKeeper !== (line === 'goal')) return null;

  const slots = pitch[line];
  const count = slots.length;
  const hovered = Math.min(count - 1, Math.max(0, Math.floor(x * count)));
  const slotWidth = 1 / count;
  const isDirectHit =
    slots[hovered] !== null &&
    Math.abs(x - slotX(line, hovered)) <= DIRECT_HIT_FRACTION * slotWidth;
  if (isDirectHit) return { line, slot: hovered };

  let nearestFree: number | null = null;
  let nearestDistance = Infinity;
  for (let slot = 0; slot < count; slot += 1) {
    if (slots[slot] !== null) continue;
    const distance = Math.abs(x - slotX(line, slot));
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestFree = slot;
    }
  }
  if (nearestFree !== null) return { line, slot: nearestFree };
  // The line is full: target the hovered occupied slot (replace/swap).
  return { line, slot: hovered };
}

// Places playerId into the target slot. If the target is occupied, the
// occupant swaps into the dragged player's old slot when the drag started on
// the pitch, or leaves the pitch (back to the bench) when it started off it.
export function applyDrop(
  pitch: PitchState,
  playerId: string,
  target: DropTarget,
): PitchState {
  const occupantId = pitch[target.line][target.slot];
  if (occupantId === playerId) return pitch;

  const origin = findSlot(pitch, playerId);
  const next: PitchState = {
    goal: [...pitch.goal],
    def: [...pitch.def],
    mid: [...pitch.mid],
    att: [...pitch.att],
  };
  if (origin) next[origin.line][origin.slot] = occupantId;
  next[target.line][target.slot] = playerId;
  return next;
}

export function removeFromPitch(
  pitch: PitchState,
  playerId: string,
): PitchState {
  const origin = findSlot(pitch, playerId);
  if (!origin) return pitch;
  const next: PitchState = {
    goal: [...pitch.goal],
    def: [...pitch.def],
    mid: [...pitch.mid],
    att: [...pitch.att],
  };
  next[origin.line][origin.slot] = null;
  return next;
}

// Arranges starters by their position attribute: GK to goal, outfielders on
// their own line left to right, spilling to adjacent lines when full. Extra
// goalkeepers stay off the pitch (the backend forbids them anyway).
export function autoArrange(starters: Player[]): PitchState {
  const pitch = createEmptyPitch();
  for (const player of starters) {
    if (player.position === 'GK') {
      if (pitch.goal[0] === null) pitch.goal[0] = player.id;
      continue;
    }
    for (const line of POSITION_LINES[player.position]) {
      const free = pitch[line].indexOf(null);
      if (free !== -1) {
        pitch[line][free] = player.id;
        break;
      }
    }
  }
  return pitch;
}

export function placedIds(pitch: PitchState): string[] {
  return LINE_BANDS.flatMap(({ line }) =>
    pitch[line].filter((id): id is string => id !== null),
  );
}

// Formation read off slot occupancy (e.g. "4-3-3"), null while the outfield
// is empty so the UI can show a placeholder.
export function deriveFormation(pitch: PitchState): string | null {
  const counts = FORMATION_LINES.map(
    (line) => pitch[line].filter((id) => id !== null).length,
  );
  if (counts.every((count) => count === 0)) return null;
  return counts.join('-');
}

// Slots are valid by construction (only a GK can occupy the goal), so a full
// XI just needs 11 placed players including the goalkeeper.
export function isValidXi(pitch: PitchState): boolean {
  return (
    placedIds(pitch).length === REQUIRED_STARTERS && pitch.goal[0] !== null
  );
}
