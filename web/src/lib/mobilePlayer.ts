import { getDeviceKind, isTV, type DeviceKind } from './device';
export function isPhonePlayer(): boolean {
    return getDeviceKind() === 'phone' && !isTV();
}

export function resolveSurfaceTap(kind: DeviceKind): 'toggle-controls' | 'toggle-play' {
    return kind === 'phone' ? 'toggle-controls' : 'toggle-play';
}

export function shouldUseWebkitFullscreenFallback(
    isPhone: boolean,
    fullscreenEnabled: boolean,
    hasWebkitEnterFullscreen: boolean,
): boolean {
    return isPhone && !fullscreenEnabled && hasWebkitEnterFullscreen;
}

export function sliderRatio(
    rect: { left: number; top: number; width: number; height: number },
    clientX: number,
    clientY: number,
    rotated: boolean,
): number {
    const offset = rotated ? clientY - rect.top : clientX - rect.left;
    const length = rotated ? rect.height : rect.width;
    if (length <= 0) return 0;
    return Math.min(1, Math.max(0, offset / length));
}
