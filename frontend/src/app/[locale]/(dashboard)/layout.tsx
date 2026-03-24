import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar, Header } from "@/components/layout";
import { AuthGuard } from "@/features/auth";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <Header />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
