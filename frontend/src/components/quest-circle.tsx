"use client";

import { Check, Lock } from "lucide-react";

export type CircleState = "done" | "current" | "available" | "locked";

export function QuestCircle({
  state,
  content,
  size = 60,
  onClick,
  label,
}: {
  state: CircleState;
  content: React.ReactNode;
  size?: number;
  onClick?: () => void;
  label?: string;
}) {
  const cls = `eq-circle ${state}`;
  const inner =
    state === "done" ? (
      <Check size={Math.round(size * 0.4)} strokeWidth={2} />
    ) : state === "locked" ? (
      <Lock size={Math.round(size * 0.36)} strokeWidth={1.75} />
    ) : (
      content
    );

  const style = { width: size, height: size };

  if (state === "locked") {
    return (
      <div className={cls} style={style} aria-label={label}>
        {inner}
      </div>
    );
  }

  return (
    <button type="button" className={cls} style={style} onClick={onClick} aria-label={label}>
      {inner}
    </button>
  );
}
