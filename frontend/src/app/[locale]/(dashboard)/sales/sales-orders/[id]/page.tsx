import { SODetailPage } from "@/features/sales";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <SODetailPage params={params} />;
}
