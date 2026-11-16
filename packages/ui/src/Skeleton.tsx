// Shown while any async region loads, per the plan's "every async region
// has a skeleton" rule. A single shimmer-free bar keeps the no-animation
// visual rule from section 13 intact.
export function Skeleton({ height = 20, width = "100%" }: { height?: number; width?: string | number }) {
  return (
    <div
      style={{ height, width, background: "var(--cb-line)", opacity: 0.4, borderRadius: 2 }}
      aria-hidden="true"
    />
  );
}
