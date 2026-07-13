import type { Player, PlayerPosition } from '@/lib/api';

export type LineId = 'goal' | 'def' | 'mid' | 'att';

// Each line holds a dense, ordered list of player ids (no empty slots). The
// list length is what drives the on-pitch layout: players are centered with a
// fixed gap, so one sits dead center, two straddle the center, and so on.
export type PitchState = Record<LineId, string[]>;

export type DropTarget =
  | { line: LineId; mode: 'insert'; index: number }
  | { line: LineId; mode: 'replace'; targetId: string };

export const REQUIRED_STARTERS = 11;

export const LINE_CAPACITY: Record<LineId, number> = {
  goal: 1,
  def: 6,
  mid: 6,
  att: 6,
};

// Horizontal gap between adjacent players on a line, as a fraction of the
// pitch width. Six players span 5 gaps (0.1 to 0.9), leaving a small margin.
const LINE_GAP = 0.16;

// A drop within this fraction of a player's center (horizontally) lands "on"
// that player and replaces/swaps them; otherwise it inserts between players.
const HIT_RADIUS = 0.06;

// Vertical bands of the pitch, top to bottom (attack at the top, own goal at
// the bottom). Fractions of the pitch height; the bands partition [0, 1].
export const LINE_BANDS: { line: LineId; from: number; to: number }[] = [
  { line: 'att', from: 0, to: 0.3 },
  { line: 'mid', from: 0.3, to: 0.58 },
  { line: 'def', from: 0.58, to: 0.84 },
  { line: 'goal', from: 0.84, to: 1 },
];

// Order a formation string reads (e.g. "4-3-3").
const FORMATION_LINES: LineId[] = ['def', 'mid', 'att'];

// Preferred line per outfield position, then where overflow spills to.
const POSITION_LINES: Record<Exclude<PlayerPosition, 'GK'>, LineId[]> = {
  DEF: ['def', 'mid', 'att'],
  MID: ['mid', 'def', 'att'],
  ATT: ['att', 'mid', 'def'],
};

export function createEmptyPitch(): PitchState {
  return { goal: [], def: [], mid: [], att: [] };
}

function clonePitch(pitch: PitchState): PitchState {
  return {
    goal: [...pitch.goal],
    def: [...pitch.def],
    mid: [...pitch.mid],
    att: [...pitch.att],
  };
}

// Horizontal center of the player at `index` of `count` players on a line, as
// a fraction of the pitch width. Centers the group around 0.5.
export function playerX(index: number, count: number): number {
  return 0.5 + (index - (count - 1) / 2) * LINE_GAP;
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

export function findLineOf(pitch: PitchState, playerId: string): LineId | null {
  for (const { line } of LINE_BANDS) {
    if (pitch[line].includes(playerId)) return line;
  }
  return null;
}

// Resolves a drop at normalized coordinates (x, y in [0, 1]) to a target, or
// null when the drop is not allowed: only goalkeepers may target the goal
// band, and goalkeepers may target nothing else. A drop lands on a player
// (replace/swap) or between players (insert); a full line always replaces.
export function resolveDrop(args: {
  x: number;
  y: number;
  playerPosition: PlayerPosition;
  pitch: PitchState;
  draggingId: string | null;
}): DropTarget | null {
  const { x, y, playerPosition, pitch, draggingId } = args;
  const line = lineAt(y);
  const isKeeper = playerPosition === 'GK';
  if (isKeeper !== (line === 'goal')) return null;

  const current = pitch[line];
  const count = current.length;
  const nearest = nearestPlayer(current, x, count, draggingId);
  if (nearest && nearest.distance <= HIT_RADIUS) {
    return { line, mode: 'replace', targetId: nearest.id };
  }

  const others = current.filter((id) => id !== draggingId);
  if (others.length >= LINE_CAPACITY[line]) {
    return nearest
      ? { line, mode: 'replace', targetId: nearest.id }
      : { line, mode: 'insert', index: 0 };
  }

  let index = 0;
  current.forEach((id, i) => {
    if (id !== draggingId && playerX(i, count) < x) index += 1;
  });
  return { line, mode: 'insert', index };
}

function nearestPlayer(
  line: string[],
  x: number,
  count: number,
  draggingId: string | null,
): { id: string; distance: number } | null {
  let nearest: { id: string; distance: number } | null = null;
  line.forEach((id, i) => {
    if (id === draggingId) return;
    const distance = Math.abs(x - playerX(i, count));
    if (!nearest || distance < nearest.distance) nearest = { id, distance };
  });
  return nearest;
}

// Places playerId at the target. Insert drops splice the player into the line;
// replace drops swap with the occupant when the dragged player comes from
// another line, or bump the occupant to the bench when it comes from off the
// pitch. A same-line replace just reorders.
export function applyDrop(
  pitch: PitchState,
  playerId: string,
  target: DropTarget,
): PitchState {
  if (target.mode === 'replace' && target.targetId === playerId) return pitch;

  const origin = findLineOf(pitch, playerId);
  const next = clonePitch(pitch);
  const originIndex = origin ? next[origin].indexOf(playerId) : -1;
  if (origin) next[origin].splice(originIndex, 1);
  const targetLine = next[target.line];

  if (target.mode === 'insert') {
    targetLine.splice(clamp(target.index, targetLine.length), 0, playerId);
    return next;
  }

  const occupantIndex = targetLine.indexOf(target.targetId);
  if (occupantIndex === -1) {
    targetLine.push(playerId);
  } else if (origin && origin !== target.line) {
    targetLine[occupantIndex] = playerId;
    next[origin].splice(clamp(originIndex, next[origin].length), 0, target.targetId);
  } else if (origin === target.line) {
    targetLine.splice(occupantIndex, 0, playerId);
  } else {
    targetLine[occupantIndex] = playerId;
  }
  return next;
}

function clamp(index: number, max: number): number {
  return Math.max(0, Math.min(index, max));
}

export function removeFromPitch(
  pitch: PitchState,
  playerId: string,
): PitchState {
  const origin = findLineOf(pitch, playerId);
  if (!origin) return pitch;
  const next = clonePitch(pitch);
  next[origin].splice(next[origin].indexOf(playerId), 1);
  return next;
}

// Arranges starters by their position attribute: GK to goal, outfielders on
// their own line, spilling to adjacent lines when full. Extra goalkeepers stay
// off the pitch (the backend forbids them anyway).
export function autoArrange(starters: Player[]): PitchState {
  const pitch = createEmptyPitch();
  for (const player of starters) {
    if (player.position === 'GK') {
      if (pitch.goal.length < LINE_CAPACITY.goal) pitch.goal.push(player.id);
      continue;
    }
    for (const line of POSITION_LINES[player.position]) {
      if (pitch[line].length < LINE_CAPACITY[line]) {
        pitch[line].push(player.id);
        break;
      }
    }
  }
  return pitch;
}

export function placedIds(pitch: PitchState): string[] {
  return LINE_BANDS.flatMap(({ line }) => pitch[line]);
}

// Formation read off the outfield line counts (e.g. "4-3-3"), null while the
// outfield is empty so the UI can show a placeholder.
export function deriveFormation(pitch: PitchState): string | null {
  const counts = FORMATION_LINES.map((line) => pitch[line].length);
  if (counts.every((count) => count === 0)) return null;
  return counts.join('-');
}

// Lines are valid by construction (only a GK can occupy the goal), so a full
// XI just needs 11 placed players including the goalkeeper.
export function isValidXi(pitch: PitchState): boolean {
  return placedIds(pitch).length === REQUIRED_STARTERS && pitch.goal.length === 1;
}
