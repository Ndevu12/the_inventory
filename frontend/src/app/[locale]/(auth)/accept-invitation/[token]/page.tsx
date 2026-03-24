"use client"

import { use } from "react"
import { AcceptInvitationPage } from "@/features/settings/pages/accept-invitation-page"

export default function AcceptInvitationRoute({
  params,
}: {
  params: Promise<{ token: string }>
}) {
  const { token } = use(params)
  return <AcceptInvitationPage token={token} />
}
