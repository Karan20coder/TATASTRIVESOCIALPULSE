import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";

export function useCanvasSetup() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rect = useRef<{ width: number; height: number }>({ width: 0, height: 0 });
  const isVisible = useRef<boolean>(true);
  const prefersReduced = useReducedMotion();
  const [reducedMotion, setReducedMotion] = useState(Boolean(prefersReduced));

  useEffect(() => {
    setReducedMotion(Boolean(prefersReduced));
  }, [prefersReduced]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // ResizeObserver to track dimensions without reflow
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        rect.current = { width, height };
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
      }
    });
    ro.observe(canvas);

    // IntersectionObserver to pause rendering when off-screen
    const io = new IntersectionObserver(([entry]) => {
      isVisible.current = entry.isIntersecting;
    });
    io.observe(canvas);

    return () => {
      ro.disconnect();
      io.disconnect();
    };
  }, []);

  return { canvasRef, rect, isVisible, reducedMotion };
}
