"use client";

import dynamic from "next/dynamic";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AppLoadingSkeleton } from "@/components/ui/Skeleton";

const AppShell = dynamic(() => import("@/components/AppShell"), {
  ssr: false,
  loading: () => <AppLoadingSkeleton />
});

export default function Page() {
  return (
    <ErrorBoundary>
      <AppShell />
    </ErrorBoundary>
  );
}
