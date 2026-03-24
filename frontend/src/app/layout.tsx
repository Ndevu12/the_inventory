import "./globals.css";

import { DEFAULT_LOCALE } from "@/i18n/routing";

/**
 * Root layout must include `<html>` and `<body>` (Next.js requirement).
 * Locale-specific `lang` / `dir` are updated client-side in `LocaleLayoutShell`.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang={DEFAULT_LOCALE} dir="ltr" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
