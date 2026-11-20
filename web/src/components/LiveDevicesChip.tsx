import { usePlaybackCount } from "../lib/api";

export interface LiveDevicesPresentation {
  color: string;
  desktopText: string;
  phoneText: string;
}

export function getLiveDevicesPresentation(
  active: number,
  limit: number,
): LiveDevicesPresentation {
  const color =
    active >= 3
      ? "#f43f5e"
      : active === 2
        ? "#fbbf24"
        : active === 1
          ? "#34d399"
          : "#9ca3af";

  return {
    color,
    desktopText: `${active} watching`,
    phoneText: `${active}/${limit}`,
  };
}

export default function LiveDevicesChip() {
  const { data } = usePlaybackCount();
  if (!data) return null;

  const presentation = getLiveDevicesPresentation(data.active, data.limit);
  return (
    <span
      role="status"
      aria-live="polite"
      tabIndex={-1}
      className="inline-flex items-center gap-1.5 rounded-full border border-[#2b3a38] bg-[#141d1c] px-2.5 py-1 text-[11px] font-bold tracking-wide text-[#9db6b1] sm:gap-2 sm:px-3 sm:text-xs"
    >
      <span
        aria-hidden="true"
        className="h-1.5 w-1.5 shrink-0 rounded-full"
        style={{ backgroundColor: presentation.color }}
      />
      <span className="hidden sm:inline">{presentation.desktopText}</span>
      <span className="sm:hidden">{presentation.phoneText}</span>
    </span>
  );
}
