import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return <div className={cn("shimmer rounded-lg", className)} />;
}

export function MessageSkeleton() {
  return (
    <div className="flex gap-3 py-3">
      <Skeleton className="w-7 h-7 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2 max-w-lg">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    </div>
  );
}

export function DocumentCardSkeleton() {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl border border-border bg-card">
      <Skeleton className="w-9 h-9 rounded-xl shrink-0" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-3.5 w-48" />
        <Skeleton className="h-3 w-32" />
      </div>
      <Skeleton className="h-5 w-16 rounded-full" />
    </div>
  );
}

export function ReportCardSkeleton() {
  return (
    <div className="p-3 rounded-xl border border-border bg-card space-y-2">
      <div className="flex gap-2">
        <Skeleton className="w-3.5 h-3.5 rounded-full shrink-0" />
        <Skeleton className="h-3.5 flex-1" />
      </div>
      <Skeleton className="h-3 w-24" />
      <Skeleton className="h-3 w-20" />
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="p-4 rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="w-4 h-4 rounded" />
      </div>
      <Skeleton className="h-7 w-12" />
    </div>
  );
}
