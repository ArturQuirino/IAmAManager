import { describe, expect, it } from 'vitest';
import type { Player, PlayerPosition } from '@/lib/api';
import {
  applyDrop,
  autoArrange,
  createEmptyPitch,
  deriveFormation,
  findLineOf,
  isValidXi,
  placedIds,
  playerX,
  removeFromPitch,
  resolveDrop,
  type PitchState,
} from '@/lib/tactics';

function player(id: string, position: PlayerPosition): Player {
  return {
    id,
    name: id,
    position,
    pace: 70,
    shooting: 70,
    passing: 70,
    dribbling: 70,
    defending: 70,
    physical: 70,
    overall: 70,
  };
}

// A valid starting XI in a 4-3-3.
function startingXi(): Player[] {
  return [
    player('gk', 'GK'),
    ...['d0', 'd1', 'd2', 'd3'].map((id) => player(id, 'DEF')),
    ...['m0', 'm1', 'm2'].map((id) => player(id, 'MID')),
    ...['a0', 'a1', 'a2'].map((id) => player(id, 'ATT')),
  ];
}

// Vertical center of each band (see LINE_BANDS): att .15, mid .44, def .71.
const Y = { att: 0.15, mid: 0.44, def: 0.71, goal: 0.95 };

describe('playerX', () => {
  it('centers a single player and straddles the center for two', () => {
    expect(playerX(0, 1)).toBeCloseTo(0.5);
    expect(playerX(0, 2)).toBeCloseTo(0.42);
    expect(playerX(1, 2)).toBeCloseTo(0.58);
  });

  it('spreads three symmetrically around the center', () => {
    expect(playerX(0, 3)).toBeCloseTo(0.34);
    expect(playerX(1, 3)).toBeCloseTo(0.5);
    expect(playerX(2, 3)).toBeCloseTo(0.66);
  });
});

describe('autoArrange', () => {
  it('places the GK in goal and outfielders on their lines, densely', () => {
    const pitch = autoArrange(startingXi());
    expect(pitch.goal).toEqual(['gk']);
    expect(pitch.def).toEqual(['d0', 'd1', 'd2', 'd3']);
    expect(pitch.mid).toEqual(['m0', 'm1', 'm2']);
    expect(pitch.att).toEqual(['a0', 'a1', 'a2']);
  });

  it('spills a seventh defender onto the adjacent line', () => {
    const starters = [
      player('gk', 'GK'),
      ...Array.from({ length: 7 }, (_, i) => player(`d${i}`, 'DEF')),
      ...Array.from({ length: 3 }, (_, i) => player(`a${i}`, 'ATT')),
    ];
    const pitch = autoArrange(starters);
    expect(pitch.def).toEqual(['d0', 'd1', 'd2', 'd3', 'd4', 'd5']);
    expect(pitch.mid).toEqual(['d6']);
    expect(pitch.att).toEqual(['a0', 'a1', 'a2']);
  });

  it('leaves extra goalkeepers off the pitch', () => {
    const pitch = autoArrange([player('gk1', 'GK'), player('gk2', 'GK')]);
    expect(pitch.goal).toEqual(['gk1']);
    expect(placedIds(pitch)).toEqual(['gk1']);
  });
});

describe('resolveDrop', () => {
  const base = { pitch: createEmptyPitch(), draggingId: null };

  it('picks the line from the vertical band under the drop', () => {
    const args = { ...base, x: 0.5, playerPosition: 'MID' as const };
    expect(resolveDrop({ ...args, y: Y.att })?.line).toBe('att');
    expect(resolveDrop({ ...args, y: Y.mid })?.line).toBe('mid');
    expect(resolveDrop({ ...args, y: Y.def })?.line).toBe('def');
  });

  it('inserts into an empty line at index 0', () => {
    expect(
      resolveDrop({ ...base, x: 0.5, y: Y.mid, playerPosition: 'MID' }),
    ).toEqual({ line: 'mid', mode: 'insert', index: 0 });
  });

  it('replaces the player under a direct hit', () => {
    const pitch = autoArrange(startingXi()); // mid centers: .34 .5 .66
    expect(
      resolveDrop({ pitch, draggingId: null, x: 0.34, y: Y.mid, playerPosition: 'ATT' }),
    ).toEqual({ line: 'mid', mode: 'replace', targetId: 'm0' });
  });

  it('inserts by x-order between and around players', () => {
    const pitch = autoArrange(startingXi());
    const drop = (x: number) =>
      resolveDrop({ pitch, draggingId: null, x, y: Y.mid, playerPosition: 'ATT' });
    expect(drop(0.02)).toEqual({ line: 'mid', mode: 'insert', index: 0 });
    expect(drop(0.42)).toEqual({ line: 'mid', mode: 'insert', index: 1 });
    expect(drop(0.98)).toEqual({ line: 'mid', mode: 'insert', index: 3 });
  });

  it('replaces on a full line even without a direct hit', () => {
    let pitch = createEmptyPitch();
    pitch = { ...pitch, mid: ['a', 'b', 'c', 'd', 'e', 'f'] };
    const target = resolveDrop({
      pitch,
      draggingId: null,
      x: 0.5,
      y: Y.mid,
      playerPosition: 'MID',
    });
    expect(target?.mode).toBe('replace');
  });

  it('excludes the dragged player when repositioning within a line', () => {
    const pitch = autoArrange(startingXi());
    // Dragging m1 to the far left inserts before m0, never "hits" itself.
    expect(
      resolveDrop({ pitch, draggingId: 'm1', x: 0.02, y: Y.mid, playerPosition: 'MID' }),
    ).toEqual({ line: 'mid', mode: 'insert', index: 0 });
  });

  it('rejects goalkeepers outside the goal and outfielders in it', () => {
    expect(
      resolveDrop({ ...base, x: 0.5, y: Y.mid, playerPosition: 'GK' }),
    ).toBeNull();
    expect(
      resolveDrop({ ...base, x: 0.5, y: Y.goal, playerPosition: 'DEF' }),
    ).toBeNull();
  });

  it('lets a goalkeeper drop into the goal', () => {
    expect(
      resolveDrop({ ...base, x: 0.5, y: Y.goal, playerPosition: 'GK' }),
    ).toEqual({ line: 'goal', mode: 'insert', index: 0 });
  });
});

describe('applyDrop', () => {
  it('inserts a player at the given index', () => {
    let pitch = createEmptyPitch();
    pitch = applyDrop(pitch, 'm0', { line: 'mid', mode: 'insert', index: 0 });
    pitch = applyDrop(pitch, 'm1', { line: 'mid', mode: 'insert', index: 1 });
    pitch = applyDrop(pitch, 'x', { line: 'mid', mode: 'insert', index: 1 });
    expect(pitch.mid).toEqual(['m0', 'x', 'm1']);
  });

  it('moves a placed player to another line, keeping lines dense', () => {
    let pitch = applyDrop(createEmptyPitch(), 'a0', { line: 'att', mode: 'insert', index: 0 });
    pitch = applyDrop(pitch, 'a0', { line: 'mid', mode: 'insert', index: 0 });
    expect(pitch.att).toEqual([]);
    expect(pitch.mid).toEqual(['a0']);
  });

  it('sends the occupant to the bench when replacing from the bench', () => {
    let pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', mode: 'insert', index: 0 });
    pitch = applyDrop(pitch, 'bench', { line: 'mid', mode: 'replace', targetId: 'm0' });
    expect(pitch.mid).toEqual(['bench']);
    expect(findLineOf(pitch, 'm0')).toBeNull();
  });

  it('swaps players across lines, preserving both counts', () => {
    let pitch = applyDrop(createEmptyPitch(), 'd0', { line: 'def', mode: 'insert', index: 0 });
    pitch = applyDrop(pitch, 'a0', { line: 'att', mode: 'insert', index: 0 });
    pitch = applyDrop(pitch, 'd0', { line: 'att', mode: 'replace', targetId: 'a0' });
    expect(pitch.att).toEqual(['d0']);
    expect(pitch.def).toEqual(['a0']);
  });

  it('reorders within a line when replacing a same-line player', () => {
    let pitch = createEmptyPitch();
    ['m0', 'm1', 'm2'].forEach((id, index) => {
      pitch = applyDrop(pitch, id, { line: 'mid', mode: 'insert', index });
    });
    pitch = applyDrop(pitch, 'm2', { line: 'mid', mode: 'replace', targetId: 'm0' });
    expect(pitch.mid).toEqual(['m2', 'm0', 'm1']);
  });

  it('is a no-op when replacing a player with itself', () => {
    const pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', mode: 'insert', index: 0 });
    expect(applyDrop(pitch, 'm0', { line: 'mid', mode: 'replace', targetId: 'm0' })).toBe(pitch);
  });
});

describe('removeFromPitch', () => {
  it('clears the player and ignores players not on the pitch', () => {
    const pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', mode: 'insert', index: 0 });
    expect(removeFromPitch(pitch, 'm0').mid).toEqual([]);
    expect(removeFromPitch(pitch, 'ghost')).toBe(pitch);
  });
});

describe('derived values', () => {
  it('derives the formation from the line counts', () => {
    expect(deriveFormation(createEmptyPitch())).toBeNull();
    expect(deriveFormation(autoArrange(startingXi()))).toBe('4-3-3');
  });

  it('validates eleven placed players including the goalkeeper', () => {
    const full = autoArrange(startingXi());
    expect(isValidXi(full)).toBe(true);
    expect(placedIds(full)).toHaveLength(11);
    expect(isValidXi(removeFromPitch(full, 'a0'))).toBe(false);
    expect(isValidXi(removeFromPitch(full, 'gk'))).toBe(false);
  });

  it('allows up to six players on an outfield line', () => {
    let pitch = createEmptyPitch();
    const sixth = Array.from({ length: 6 }, (_, i) => `d${i}`);
    sixth.forEach((id, index) => {
      pitch = applyDrop(pitch, id, { line: 'def', mode: 'insert', index });
    });
    expect(pitch.def).toHaveLength(6);
    // A seventh drop (not a direct hit) replaces rather than overflows.
    const target = resolveDrop({
      pitch,
      draggingId: null,
      x: playerX(0, 6),
      y: Y.def,
      playerPosition: 'DEF',
    });
    expect(target?.mode).toBe('replace');
  });
});
