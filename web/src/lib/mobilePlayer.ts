import { getDeviceKind, isTV, type DeviceKind } from './device';

export type PlayerDragSide = 'left' | 'right';

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

export function shouldClaimVerticalDrag(deltaX: number, deltaY: number): boolean {
    return Math.abs(deltaY) > 12 && Math.abs(deltaY) > 1.3 * Math.abs(deltaX);
}

export function calculateDragValue(
    startValue: number,
    startY: number,
    currentY: number,
    stageHeight: number,
): number {
    if (!Number.isFinite(stageHeight) || stageHeight <= 0
        || !Number.isFinite(startValue) || !Number.isFinite(startY) || !Number.isFinite(currentY)) {
        return clampVolume(startValue);
    }
    return clampVolume(startValue + (startY - currentY) / (0.65 * stageHeight));
}

export function clampBrightness(value: number): number {
    return Number.isFinite(value) ? Math.min(1, Math.max(0.1, value)) : 1;
}

export function clampVolume(value: number): number {
    return Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
}

export function selectDragSide(clientX: number, stageLeft: number, stageWidth: number): PlayerDragSide {
    return clientX < stageLeft + stageWidth / 2 ? 'left' : 'right';
}

export function shouldUseDeviceVolumeButtons(isPhone: boolean, volumeWritable: boolean | null): boolean {
    return isPhone && volumeWritable !== true;
}
