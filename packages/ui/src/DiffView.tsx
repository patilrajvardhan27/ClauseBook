import type { DiffHunk } from "@clausebook/api-client";

const COLOR_BY_OP: Record<DiffHunk["op"], string | undefined> = {
  equal: undefined,
  insert: "var(--cb-green)",
  delete: "var(--cb-red)",
};

// Renders word-level diff hunks the way Word shows a tracked change:
// struck-through deletions, underlined insertions, plain equal runs.
export function DiffView({ hunks }: { hunks: DiffHunk[] }) {
  return (
    <p style={{ lineHeight: 1.6 }}>
      {hunks.map((hunk, index) => {
        const color = COLOR_BY_OP[hunk.op];
        const style: React.CSSProperties = { color };
        if (hunk.op === "delete") style.textDecoration = "line-through";
        if (hunk.op === "insert") style.textDecoration = "underline";
        return (
          <span key={index} style={style}>
            {hunk.text}
          </span>
        );
      })}
    </p>
  );
}
