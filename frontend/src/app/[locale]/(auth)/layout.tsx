import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-muted/40">
      <div className="absolute end-4 top-4 z-10">
        <LanguageSwitcher />
      </div>
      {children}
    </div>
  );
}
