import type { Metadata } from "next";
import { Providers } from "@/lib/providers";
import { APP_NAME } from "@/lib/utils/constants";
import "./globals.css";

export const metadata: Metadata = {
  title: APP_NAME,
  description: "Multi-tenant inventory management system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
