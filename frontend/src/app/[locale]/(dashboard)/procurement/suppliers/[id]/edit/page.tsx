import { SupplierEditPage } from "@/features/procurement";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <SupplierEditPage params={params} />;
}
