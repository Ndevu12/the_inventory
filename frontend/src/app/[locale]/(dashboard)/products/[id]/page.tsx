import { ProductDetailPage } from "@/features/inventory"

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <ProductDetailPage params={params} />
}
