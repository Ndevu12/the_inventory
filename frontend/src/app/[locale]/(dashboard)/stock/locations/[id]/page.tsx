import { LocationDetailPage } from "@/features/inventory"

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return <LocationDetailPage params={params} />
}
