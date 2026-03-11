"use client";

import Image from "next/image";
import { useState } from "react";

export function HeroIllustration() {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="relative w-full min-h-[280px] lg:min-h-[360px] flex items-center justify-center">
      {!imgError ? (
        <Image
          src="/illustrations/hero-data-forge.png"
          alt="Data Forge"
          width={480}
          height={360}
          className="object-contain max-h-[360px] w-auto"
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-full max-w-md aspect-[4/3] rounded-2xl bg-gradient-to-br from-[var(--brand-teal)]/20 to-[var(--brand-deep-blue)]/20 border border-[var(--brand-teal)]/30 flex items-center justify-center">
          <svg
            className="w-24 h-24 text-[var(--brand-teal)]/60"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
            />
          </svg>
        </div>
      )}
    </div>
  );
}
