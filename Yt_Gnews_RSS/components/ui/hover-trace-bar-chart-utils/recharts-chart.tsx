"use client";

import * as React from "react";
import { ResponsiveContainer } from "recharts";

export type ChartConfig = Record<
  string,
  {
    label?: React.ReactNode;
    icon?: React.ComponentType;
    colors?: {
      light?: string[];
      dark?: string[];
    };
    color?: string;
  }
>;

interface ChartContainerProps extends React.ComponentProps<"div"> {
  config: ChartConfig;
  children: React.ReactElement;
}

export const ChartContainer = React.forwardRef<
  HTMLDivElement,
  ChartContainerProps
>(({ id, className, config, children, ...props }, ref) => {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`;

  return (
    <div
      data-chart={chartId}
      ref={ref}
      className={`flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none ${className || ""}`}
      style={
        {
          "--color-desktop-0": config.desktop?.colors?.light?.[0] || "#3ddc97",
          "--color-desktop-1": config.desktop?.colors?.dark?.[0] || "#0984e3",
          ...props.style,
        } as React.CSSProperties
      }
      {...props}
    >
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
});

ChartContainer.displayName = "ChartContainer";
