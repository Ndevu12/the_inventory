import { MovementDetailPage } from "@/features/inventory";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <MovementDetailPage params={params} />;
}
