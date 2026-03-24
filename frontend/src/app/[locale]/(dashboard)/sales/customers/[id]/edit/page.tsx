import { CustomerEditPage } from "@/features/sales";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <CustomerEditPage params={params} />;
}
