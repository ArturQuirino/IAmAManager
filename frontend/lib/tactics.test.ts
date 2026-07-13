import { describe, expect, it } from 'vitest';
import type { Player, PlayerPosition } from '@/lib/api';
import {
  applyDrop,
  autoArrange,
  createEmptyPitch,
  deriveFormation,
  findSlot,
  isValidXi,
  placedIds,
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

describe('autoArrange', () => {
  it('places the GK in goal and outfielders on their lines, left to right', () => {
    const pitch = autoArrange(startingXi());
    expect(pitch.goal).toEqual(['gk']);
    expect(pitch.def).toEqual(['d0', 'd1', 'd2', 'd3', null]);
    expect(pitch.mid).toEqual(['m0', 'm1', 'm2', null, null]);
    expect(pitch.att).toEqual(['a0', 'a1', 'a2', null, null]);
  });

  it('spills overflow beyond five onto the adjacent line', () => {
    const starters = [
      player('gk', 'GK'),
      ...Array.from({ length: 7 }, (_, i) => player(`d${i}`, 'DEF')),
      ...Array.from({ length: 3 }, (_, i) => player(`a${i}`, 'ATT')),
    ];
    const pitch = autoArrange(starters);
    expect(pitch.def).toEqual(['d0', 'd1', 'd2', 'd3', 'd4']);
    expect(pitch.mid).toEqual(['d5', 'd6', null, null, null]);
    expect(pitch.att).toEqual(['a0', 'a1', 'a2', null, null]);
  });

  it('leaves extra goalkeepers off the pitch', () => {
    const pitch = autoArrange([player('gk1', 'GK'), player('gk2', 'GK')]);
    expect(pitch.goal).toEqual(['gk1']);
    expect(placedIds(pitch)).toEqual(['gk1']);
  });
});

describe('resolveDrop', () => {
  function arrangedPitch(): PitchState {
    return autoArrange(startingXi());
  }

  it('picks the line from the vertical band under the drop', () => {
    const pitch = createEmptyPitch();
    const base = { x: 0.5, playerPosition: 'MID' as const, pitch };
    expect(resolveDrop({ ...base, y: 0.1 })?.line).toBe('att');
    expect(resolveDrop({ ...base, y: 0.45 })?.line).toBe('mid');
    expect(resolveDrop({ ...base, y: 0.7 })?.line).toBe('def');
  });

  it('snaps to the nearest free slot on the line', () => {
    const pitch = arrangedPitch();
    // mid has m0..m2 in slots 0..2; a drop at the far left edge misses the
    // direct-hit radius of slot 0 and snaps to the nearest free slot, 3.
    const target = resolveDrop({
      x: 0.02,
      y: 0.45,
      playerPosition: 'ATT',
      pitch,
    });
    expect(target).toEqual({ line: 'mid', slot: 3 });
  });

  it('targets an occupied slot on a direct hit (replace)', () => {
    const pitch = arrangedPitch();
    // Slot 0 of mid is centered at x = 0.1 and holds m0.
    const target = resolveDrop({
      x: 0.1,
      y: 0.45,
      playerPosition: 'ATT',
      pitch,
    });
    expect(target).toEqual({ line: 'mid', slot: 0 });
  });

  it('targets the hovered occupied slot when the line is full', () => {
    let pitch = createEmptyPitch();
    for (let slot = 0; slot < 5; slot += 1)
      pitch = applyDrop(pitch, `m${slot}`, { line: 'mid', slot });
    const target = resolveDrop({
      x: 0.99,
      y: 0.45,
      playerPosition: 'ATT',
      pitch,
    });
    expect(target).toEqual({ line: 'mid', slot: 4 });
  });

  it('rejects goalkeepers outside the goal and outfielders in it', () => {
    const pitch = createEmptyPitch();
    expect(
      resolveDrop({ x: 0.5, y: 0.45, playerPosition: 'GK', pitch }),
    ).toBeNull();
    expect(
      resolveDrop({ x: 0.5, y: 0.95, playerPosition: 'DEF', pitch }),
    ).toBeNull();
  });

  it('lets a goalkeeper target the goal slot', () => {
    const pitch = createEmptyPitch();
    expect(
      resolveDrop({ x: 0.5, y: 0.95, playerPosition: 'GK', pitch }),
    ).toEqual({ line: 'goal', slot: 0 });
  });
});

describe('applyDrop', () => {
  it('places a bench player into an empty slot', () => {
    const pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 2 });
    expect(pitch.mid[2]).toBe('m0');
  });

  it('moves a placed player, clearing the old slot', () => {
    let pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 0 });
    pitch = applyDrop(pitch, 'm0', { line: 'att', slot: 4 });
    expect(pitch.mid[0]).toBeNull();
    expect(pitch.att[4]).toBe('m0');
  });

  it('replaces the occupant when the dragged player comes from the bench', () => {
    let pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 0 });
    pitch = applyDrop(pitch, 'bench1', { line: 'mid', slot: 0 });
    expect(pitch.mid[0]).toBe('bench1');
    expect(findSlot(pitch, 'm0')).toBeNull();
  });

  it('swaps when both players are on the pitch', () => {
    let pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 0 });
    pitch = applyDrop(pitch, 'a0', { line: 'att', slot: 1 });
    pitch = applyDrop(pitch, 'a0', { line: 'mid', slot: 0 });
    expect(pitch.mid[0]).toBe('a0');
    expect(pitch.att[1]).toBe('m0');
  });

  it('is a no-op when dropping a player on its own slot', () => {
    const pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 0 });
    expect(applyDrop(pitch, 'm0', { line: 'mid', slot: 0 })).toBe(pitch);
  });
});

describe('removeFromPitch', () => {
  it('clears the player slot and ignores players not on the pitch', () => {
    const pitch = applyDrop(createEmptyPitch(), 'm0', { line: 'mid', slot: 0 });
    expect(removeFromPitch(pitch, 'm0').mid[0]).toBeNull();
    expect(removeFromPitch(pitch, 'ghost')).toBe(pitch);
  });
});

describe('derived values', () => {
  it('derives the formation from slot occupancy', () => {
    expect(deriveFormation(createEmptyPitch())).toBeNull();
    expect(deriveFormation(autoArrange(startingXi()))).toBe('4-3-3');
  });

  it('validates eleven placed players including the goalkeeper', () => {
    const full = autoArrange(startingXi());
    expect(isValidXi(full)).toBe(true);
    expect(isValidXi(removeFromPitch(full, 'a0'))).toBe(false);
    expect(isValidXi(removeFromPitch(full, 'gk'))).toBe(false);
    expect(placedIds(full)).toHaveLength(11);
  });
});
