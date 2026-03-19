import { ProductEditPage } from "@/features/inventory";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <ProductEditPage params={params} />;
}
