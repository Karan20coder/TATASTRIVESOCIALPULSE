"use client";

import React from "react";
import { TiltCard } from "./be-ui-tilt-card";

export default function TiltCardPreview() {
  return (
    <div className="flex items-center justify-center p-6">
      <TiltCard className="w-[320px] border border-[#4c3527] bg-[#241913] p-8 shadow-xl">
        <div className="text-xs uppercase tracking-wider text-[#D6BFA6]">News Intelligence</div>
        <h3 className="mt-2 text-2xl font-semibold text-[#F3E9D7]">Google News RSS</h3>
        <p className="mt-3 text-sm text-[#D6BFA6]">
          Interactive 3D tilt with dynamic glare lighting for verified skilling headlines.
        </p>
      </TiltCard>
    </div>
  );
}
