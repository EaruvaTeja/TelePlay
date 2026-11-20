import { afterEach, describe, expect, it } from 'vitest';
import {
    isPhonePlayer,
    classifyLockGesture,
    calculateDragValue,
    clampBrightness,
    clampVolume,
    getLockedPlaybackAction,
    resolveSurfaceTap,
    selectDragSide,
    shouldClaimVerticalDrag,
    shouldAutoUnlockControlLock,
    shouldToggleLockedPlayback,
    shouldUseDeviceVolumeButtons,
    shouldUseWebkitFullscreenFallback,
    sliderRatio,
} from '../mobilePlayer';

function setUserAgent(userAgent: string) {
    Object.defineProperty(navigator, 'userAgent', {
        configurable: true,
        value: userAgent,
    });
}

afterEach(() => {
    Reflect.deleteProperty(navigator, 'userAgent');
});

describe('isPhonePlayer', () => {
    it.each([
        ['iPhone', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'],
        ['Android phone', 'Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile Safari/537.36'],
    ])('accepts a phone user agent (%s)', (_label, userAgent) => {
        setUserAgent(userAgent);
        expect(isPhonePlayer()).toBe(true);
    });

    it.each([
        ['TV', 'Mozilla/5.0 (SMART-TV; Tizen 7.0)'],
        ['tablet', 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)'],
        ['computer', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'],
    ])('rejects a non-phone user agent (%s)', (_label, userAgent) => {
        setUserAgent(userAgent);
        expect(isPhonePlayer()).toBe(false);
    });
});

describe('shouldUseWebkitFullscreenFallback', () => {
    it.each([
        [true, false, true, true],
        [false, false, true, false],
        [true, true, true, false],
        [true, false, false, false],
    ])('requires a phone without standard fullscreen and with video fullscreen support: %o', (
        isPhone,
        fullscreenEnabled,
        hasWebkitEnterFullscreen,
        expected,
    ) => {
        expect(shouldUseWebkitFullscreenFallback(
            isPhone,
            fullscreenEnabled,
            hasWebkitEnterFullscreen,
        )).toBe(expected);
    });
});

describe('resolveSurfaceTap', () => {
    it.each([
        ['phone', 'toggle-controls'],
        ['tv', 'toggle-play'],
        ['computer', 'toggle-play'],
        ['tablet', 'toggle-play'],
    ] as const)('%s keeps its established surface action', (kind, expected) => {
        expect(resolveSurfaceTap(kind)).toBe(expected);
    });
});

describe('sliderRatio', () => {
    const rect = { left: 10, top: 20, width: 100, height: 80 };

    it('uses the horizontal axis for an unrotated slider', () => {
        expect(sliderRatio(rect, 35, 75, false)).toBeCloseTo(0.25);
    });

    it('uses the vertical axis for a rotated slider', () => {
        expect(sliderRatio(rect, 85, 40, true)).toBeCloseTo(0.25);
    });

    it.each([
        [0, 50, false, 0],
        [120, 50, false, 1],
        [50, 0, true, 0],
        [50, 120, true, 1],
    ])('clamps pointer position (%s, %s, rotated=%s)', (clientX, clientY, rotated, expected) => {
        expect(sliderRatio(rect, clientX, clientY, rotated)).toBe(expected);
    });

    it.each([
        [{ ...rect, width: 0 }, false],
        [{ ...rect, height: 0 }, true],
    ])('returns zero for a zero-sized active axis', (degenerateRect, rotated) => {
        expect(sliderRatio(degenerateRect, 50, 50, rotated)).toBe(0);
    });
});

describe('brightness and volume gesture helpers', () => {
    it.each([
        [0, 13, true],
        [0, -13, true],
        [10, 13, false],
        [10, 14, true],
        [0, 12, false],
    ])('claims only a clearly vertical drag (%s, %s)', (deltaX, deltaY, expected) => {
        expect(shouldClaimVerticalDrag(deltaX, deltaY)).toBe(expected);
    });

    it('maps vertical displacement to a clamped adjustment value', () => {
        expect(calculateDragValue(0.5, 500, 435, 1000)).toBeCloseTo(0.6);
        expect(calculateDragValue(0.5, 500, 100, 1000)).toBe(1);
        expect(calculateDragValue(0.5, 500, 900, 1000)).toBe(0);
        expect(calculateDragValue(0.5, 500, 400, 0)).toBe(0.5);
    });

    it('clamps brightness above black and volume to mute', () => {
        expect(clampBrightness(0)).toBe(0.1);
        expect(clampBrightness(0.6)).toBe(0.6);
        expect(clampBrightness(1.2)).toBe(1);
        expect(clampVolume(-0.2)).toBe(0);
        expect(clampVolume(0.6)).toBe(0.6);
        expect(clampVolume(1.2)).toBe(1);
    });

    it('selects the drag side at pointerdown using the stage midpoint', () => {
        expect(selectDragSide(149, 100, 100)).toBe('left');
        expect(selectDragSide(150, 100, 100)).toBe('right');
    });

    it('uses the device-volume hint only for phones with non-writable volume', () => {
        expect(shouldUseDeviceVolumeButtons(true, false)).toBe(true);
        expect(shouldUseDeviceVolumeButtons(true, true)).toBe(false);
        expect(shouldUseDeviceVolumeButtons(true, null)).toBe(true);
        expect(shouldUseDeviceVolumeButtons(false, false)).toBe(false);
    });
});

describe('phone lock gesture helpers', () => {
    it.each([
        [0, 0, 'tap'],
        [7, 0, 'tap'],
        [7, -7, 'ignore'],
        [8, 0, 'ignore'],
        [9, 0, 'drag'],
        [-24, 2, 'drag'],
        [0, 9, 'ignore'],
        [10, 12, 'ignore'],
    ] as const)('classifies lock movement (%s, %s)', (deltaX, deltaY, expected) => {
        expect(classifyLockGesture(deltaX, deltaY)).toBe(expected);
    });

    it.each([
        [31.9, false],
        [32, true],
        [56, true],
        [-56, false],
    ])('requires a right drag of at least 32px (%s)', (deltaX, expected) => {
        expect(shouldToggleLockedPlayback(deltaX)).toBe(expected);
    });

    it('toggles toward the opposite playback action', () => {
        expect(getLockedPlaybackAction(true)).toBe('pause');
        expect(getLockedPlaybackAction(false)).toBe('play');
    });

    it.each([
        [true, false, false, true],
        [false, true, false, true],
        [false, false, true, true],
        [false, false, false, false],
    ])('unlocks on end, error, or dialog (%s, %s, %s)', (ended, hasError, dialogOpen, expected) => {
        expect(shouldAutoUnlockControlLock(ended, hasError, dialogOpen)).toBe(expected);
    });
});
