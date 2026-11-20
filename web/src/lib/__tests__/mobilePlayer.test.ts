import { afterEach, describe, expect, it } from 'vitest';
import {
    isPhonePlayer,
    resolveSurfaceTap,
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
