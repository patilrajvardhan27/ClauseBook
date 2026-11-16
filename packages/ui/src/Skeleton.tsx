// A plain, shimmer-free loading bar shown while an async region loads.
export function Skeleton({ height = 20, width = "100%" }: { height?: number; width?: string | number }) {
  return (
    <div
      style={{ height, width, background: "var(--cb-line)", opacity: 0.4, borderRadius: 2 }}
      aria-hidden="true"
    />
  );
}
