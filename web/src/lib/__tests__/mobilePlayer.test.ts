import { afterEach, describe, expect, it, vi } from 'vitest';
import {
    computePseudoLandscape,
    isPhonePlayer,
    lockLandscape,
    resolveSurfaceTap,
    shouldAutoLandscape,
    unlockLandscape,
} from '../mobilePlayer';
import type { DeviceKind } from '../device';

const kinds: DeviceKind[] = ['phone', 'tv', 'computer', 'tablet'];

function setUserAgent(userAgent: string) {
    Object.defineProperty(navigator, 'userAgent', {
        configurable: true,
        value: userAgent,
    });
}

function setOrientation(orientation: unknown) {
    Object.defineProperty(screen, 'orientation', {
        configurable: true,
        value: orientation,
    });
}

afterEach(() => {
    Reflect.deleteProperty(navigator, 'userAgent');
    Reflect.deleteProperty(screen, 'orientation');
    Reflect.deleteProperty(document, 'fullscreenElement');
    Reflect.deleteProperty(document, 'exitFullscreen');
    vi.restoreAllMocks();
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

describe('shouldAutoLandscape', () => {
    it.each(
        kinds.flatMap(kind =>
            [true, false].flatMap(isPortrait =>
                [true, false].map(isVideo => ({ kind, isPortrait, isVideo })),
            ),
        ),
    )('restricts auto-landscape to portrait phone video: %o', ({ kind, isPortrait, isVideo }) => {
        expect(shouldAutoLandscape(isVideo, kind, isPortrait))
            .toBe(kind === 'phone' && isPortrait && isVideo);
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

describe('computePseudoLandscape', () => {
    it.each(
        kinds.flatMap(kind =>
            [true, false].flatMap(isPortrait =>
                [true, false].flatMap(enabled =>
                    [true, false].flatMap(isVideo =>
                        [true, false].map(minimized => ({
                            kind,
                            isPortrait,
                            enabled,
                            isVideo,
                            minimized,
                        })),
                    ),
                ),
            ),
        ),
    )('applies only to enabled portrait phone video outside mini mode: %o', values => {
        const { kind, isPortrait, enabled, isVideo, minimized } = values;
        expect(computePseudoLandscape(kind, isPortrait, enabled, isVideo, minimized))
            .toBe(kind === 'phone' && isPortrait && enabled && isVideo && !minimized);
    });

    it.each(
        kinds.flatMap(kind =>
            [true, false].flatMap(isPortrait =>
                [true, false].flatMap(isVideo =>
                    [true, false].flatMap(minimized =>
                        [true, false].map(lockSupported => ({
                            kind,
                            isPortrait,
                            isVideo,
                            minimized,
                            lockSupported,
                        })),
                    ),
                ),
            ),
        ),
    )('uses CSS fallback only when native lock is unsupported: %o', values => {
        const { kind, isPortrait, isVideo, minimized, lockSupported } = values;
        expect(computePseudoLandscape(
            kind,
            isPortrait,
            !lockSupported,
            isVideo,
            minimized,
        )).toBe(kind === 'phone' && isPortrait && isVideo && !minimized && !lockSupported);
    });
});

describe('native orientation lock helpers', () => {
    it('requests fullscreen before locking landscape', async () => {
        const calls: string[] = [];
        const element = document.createElement('div');
        Object.defineProperty(element, 'requestFullscreen', {
            value: vi.fn(async () => { calls.push('fullscreen'); }),
        });
        setOrientation({
            lock: vi.fn(async (value: string) => { calls.push(value); }),
        });

        await expect(lockLandscape(element)).resolves.toBe(true);
        expect(calls).toEqual(['fullscreen', 'landscape']);
    });

    it('returns false when fullscreen and orientation locking are unsupported', async () => {
        const element = document.createElement('div');
        Object.defineProperty(element, 'requestFullscreen', {
            value: vi.fn(async () => { throw new Error('unsupported'); }),
        });
        setOrientation({
            lock: vi.fn(async () => { throw new Error('unsupported'); }),
        });

        await expect(lockLandscape(element)).resolves.toBe(false);
    });

    it('unlocks orientation and exits active fullscreen without throwing', () => {
        const unlock = vi.fn();
        const exitFullscreen = vi.fn(async () => undefined);
        setOrientation({ unlock });
        Object.defineProperty(document, 'fullscreenElement', {
            configurable: true,
            value: document.createElement('div'),
        });
        Object.defineProperty(document, 'exitFullscreen', {
            configurable: true,
            value: exitFullscreen,
        });

        expect(() => unlockLandscape()).not.toThrow();
        expect(unlock).toHaveBeenCalledOnce();
        expect(exitFullscreen).toHaveBeenCalledOnce();
    });
});
