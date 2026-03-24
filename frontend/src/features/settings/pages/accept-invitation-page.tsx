"use client"

import * as React from "react"
import { useRouter } from "@/i18n/navigation"
import { toast } from "sonner"
import { Package, CheckCircle2, AlertCircle } from "lucide-react"
import { useTranslations } from "next-intl"

import { useAuthStore } from "@/lib/auth-store"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import {
  useInvitationInfo,
  useAcceptInvitation,
} from "../hooks/use-invitations"

interface AcceptInvitationPageProps {
  token: string
}

export function AcceptInvitationPage({ token }: AcceptInvitationPageProps) {
  const router = useRouter()
  const t = useTranslations("Auth")
  const tInv = useTranslations("Auth.invitation")
  const { setTokens, setUser, setTenant, setMemberships } = useAuthStore()

  const { data: info, isLoading, isError } = useInvitationInfo(token)
  const acceptMutation = useAcceptInvitation(token)

  const [username, setUsername] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [firstName, setFirstName] = React.useState("")
  const [lastName, setLastName] = React.useState("")

  function processedCopy(status: string): { title: string; description: string } | null {
    if (status === "accepted") {
      return {
        title: tInv("processed.accepted.title"),
        description: tInv("processed.accepted.description"),
      }
    }
    if (status === "cancelled") {
      return {
        title: tInv("processed.cancelled.title"),
        description: tInv("processed.cancelled.description"),
      }
    }
    if (status === "expired") {
      return {
        title: tInv("processed.expired.title"),
        description: tInv("processed.expired.description"),
      }
    }
    return null
  }

  function handleAccept(e: React.FormEvent) {
    e.preventDefault()

    const payload: Record<string, string> = {}
    if (info?.needs_account) {
      payload.username = username
      payload.password = password
      payload.first_name = firstName
      payload.last_name = lastName
    } else {
      payload.password = password
    }

    acceptMutation.mutate(payload, {
      onSuccess: (data) => {
        setTokens(data.access, data.refresh)
        setUser(data.user)
        setTenant(data.tenant.slug)
        setMemberships(
          data.memberships ?? [
            {
              tenant__id: data.tenant.id,
              tenant__name: data.tenant.name,
              tenant__slug: data.tenant.slug,
              role: data.tenant.role,
              is_default: true,
            },
          ],
        )
        toast.success(data.detail)
        router.push("/")
      },
      onError: (error) => {
        const msg =
          (error as { message?: string }).message ??
          t("acceptInvitationFailed")
        toast.error(msg)
      },
    })
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <Skeleton className="mx-auto mb-2 h-12 w-12 rounded-xl" />
            <Skeleton className="mx-auto h-6 w-48" />
            <Skeleton className="mx-auto mt-2 h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isError || !info) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-destructive/10">
              <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
            <CardTitle>{tInv("invalidTitle")}</CardTitle>
            <CardDescription>{tInv("invalidDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Button variant="outline" onClick={() => router.push("/login")}>
              {tInv("goToLogin")}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (info.status !== "pending") {
    const copy = processedCopy(info.status)
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
              <CheckCircle2 className="h-6 w-6 text-muted-foreground" />
            </div>
            <CardTitle>
              {copy?.title ?? tInv("processedUnknownTitle", { status: info.status })}
            </CardTitle>
            <CardDescription>
              {copy?.description ??
                tInv("processedUnknownDescription", { status: info.status })}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Button variant="outline" onClick={() => router.push("/login")}>
              {tInv("goToLogin")}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <Package className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-xl">
            {tInv("joinTitle", { tenant: info.tenant_name })}
          </CardTitle>
          <CardDescription>
            {tInv("invitedAs")}{" "}
            <Badge variant="secondary" className="ml-1 capitalize">
              {info.role}
            </Badge>
          </CardDescription>
          <p className="mt-1 text-xs text-muted-foreground">
            {tInv("invitationFor", { email: info.email })}
          </p>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleAccept} className="space-y-4">
            {info.needs_account && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="first-name">{tInv("firstName")}</Label>
                    <Input
                      id="first-name"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      placeholder={tInv("firstNamePlaceholder")}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="last-name">{tInv("lastName")}</Label>
                    <Input
                      id="last-name"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder={tInv("lastNamePlaceholder")}
                    />
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="username">{tInv("username")}</Label>
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={tInv("usernamePlaceholder")}
                    required
                    autoFocus
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="password">{tInv("password")}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={tInv("passwordPlaceholderNew")}
                    required
                    minLength={8}
                  />
                </div>
              </>
            )}

            {!info.needs_account && (
              <>
                <p className="text-center text-sm text-muted-foreground">
                  {tInv("existingAccountHint")}
                </p>
                <div className="grid gap-2">
                  <Label htmlFor="existing-password">{tInv("existingPassword")}</Label>
                  <Input
                    id="existing-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={tInv("existingPasswordPlaceholder")}
                    required
                  />
                </div>
              </>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={acceptMutation.isPending}
            >
              {acceptMutation.isPending
                ? tInv("joining")
                : tInv("joinTenant", { tenant: info.tenant_name })}
            </Button>

            <p className="text-center text-xs text-muted-foreground">
              {tInv("expires", {
                date: new Date(info.expires_at).toLocaleDateString(),
              })}
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
