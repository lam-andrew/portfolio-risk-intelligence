import { useEffect, useState } from "react";

/** Measure the chart, not the viewport: labels retain their size in narrow cards. */
export function useChartWidth() {
  const [node, ref] = useState<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(560);
  useEffect(() => {
    if (!node || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) setWidth(entry.contentRect.width);
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [node]);
  return { ref, width };
}
