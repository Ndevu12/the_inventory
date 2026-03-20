import { ReactNode } from "react";

interface FeaturesListProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}

export function FeaturesList({ children, title, subtitle }: FeaturesListProps) {
  return (
    <div className="flex flex-col gap-8">
      {(title || subtitle) && (
        <div>
          {title && <h2 className="text-2xl font-semibold text-foreground">{title}</h2>}
          {subtitle && <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      )}
      <div className="grid gap-4 grid-cols-1">{children}</div>
    </div>
  );
}
