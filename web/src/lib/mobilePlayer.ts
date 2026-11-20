import { getDeviceKind, isTV, type DeviceKind } from './device';

interface OrientationLock extends ScreenOrientation {
    lock?: (orientation: 'landscape') => Promise<void>;
}

export function isPhonePlayer(): boolean {
    return getDeviceKind() === 'phone' && !isTV();
}

export function resolveSurfaceTap(kind: DeviceKind): 'toggle-controls' | 'toggle-play' {
    return kind === 'phone' ? 'toggle-controls' : 'toggle-play';
}

export function shouldAutoLandscape(
    isVideo: boolean,
    kind: DeviceKind,
    isPortrait: boolean,
): boolean {
    return isVideo && kind === 'phone' && isPortrait;
}

export async function lockLandscape(el: HTMLElement): Promise<boolean> {
    try {
        if (typeof el.requestFullscreen === 'function') {
            await el.requestFullscreen();
        }
    } catch { /* fullscreen may be unavailable */ }

    try {
        if (typeof screen === 'undefined') return false;
        const orientation = screen.orientation as OrientationLock;
        if (!orientation.lock) return false;
        await orientation.lock('landscape');
        return true;
    } catch { /* orientation lock may be unsupported */ }

    return false;
}

export function unlockLandscape(): void {
    try {
        if (typeof screen !== 'undefined') (screen.orientation as OrientationLock).unlock?.();
    } catch { /* orientation unlock may be unsupported */ }

    try {
        if (typeof document !== 'undefined' && document.fullscreenElement) {
            void document.exitFullscreen?.().catch(() => { /* fullscreen exit may be unavailable */ });
        }
    } catch { /* fullscreen exit may be unavailable */ }
}

export function computePseudoLandscape(
    kind: DeviceKind,
    isPortrait: boolean,
    enabled: boolean,
    isVideo: boolean,
    minimized: boolean,
): boolean {
    return kind === 'phone' && isPortrait && enabled && isVideo && !minimized;
}
