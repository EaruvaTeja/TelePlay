import { getDeviceKind, isTV, type DeviceKind } from './device';

export type PlayerDragSide = 'left' | 'right';
export type LockGestureClassification = 'tap' | 'drag' | 'ignore';
export type LockNoticeAction = 'locked' | 'paused' | 'playing';

export const LOCK_HOLD_TO_UNLOCK_MS = 1000;

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

export function classifyLockGesture(deltaX: number, deltaY: number): LockGestureClassification {
    const horizontal = Math.abs(deltaX);
    const vertical = Math.abs(deltaY);
    if (Math.sqrt(horizontal * horizontal + vertical * vertical) < 8) return 'tap';
    if (horizontal > 8 && horizontal > vertical) return 'drag';
    return 'ignore';
}

export function shouldToggleLockedPlayback(deltaX: number): boolean {
    return Number.isFinite(deltaX) && deltaX >= 32;
}

export function getLockHoldProgress(elapsedMs: number): number {
    if (!Number.isFinite(elapsedMs)) return 0;
    return Math.min(1, Math.max(0, elapsedMs / LOCK_HOLD_TO_UNLOCK_MS));
}

export function shouldUnlockAfterLockHold(elapsedMs: number): boolean {
    return Number.isFinite(elapsedMs) && elapsedMs >= LOCK_HOLD_TO_UNLOCK_MS;
}

export function getLockedDragProgress(deltaX: number): number {
    if (!Number.isFinite(deltaX)) return 0;
    return Math.min(1, Math.max(0, deltaX / 32));
}

export function getLockNotice(action: LockNoticeAction): { title: string; subtitle: string } {
    if (action === 'paused') {
        return { title: 'Paused', subtitle: 'Still locked. Drag right to play.' };
    }
    if (action === 'playing') {
        return { title: 'Playing', subtitle: 'Still locked. Drag right to pause.' };
    }
    return { title: 'Locked', subtitle: 'Hold lock 1s to unlock.' };
}

export function getLockedPlaybackAction(isPlaying: boolean): 'pause' | 'play' {
    return isPlaying ? 'pause' : 'play';
}

export function shouldAutoUnlockControlLock(
    videoEnded: boolean,
    hasError: boolean,
    dialogOpen: boolean,
): boolean {
    return videoEnded || hasError || dialogOpen;
}
