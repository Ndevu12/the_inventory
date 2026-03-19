import { PODetailPage } from "@/features/procurement";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <PODetailPage params={params} />;
}
