import { CycleDetailPage } from "@/features/cycle-counts";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <CycleDetailPage params={params} />;
}
