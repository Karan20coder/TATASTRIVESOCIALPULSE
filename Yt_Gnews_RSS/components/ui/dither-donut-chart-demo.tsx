import DitherDonutChart from "@/components/ui/dither-donut-chart";

export default function DitherDonutChartDemo() {
  return (
    <div className="w-full h-screen flex items-center justify-center bg-neutral-950 p-6">
      <div className="w-full max-w-sm">
        <DitherDonutChart theme="dark" />
      </div>
    </div>
  );
}
