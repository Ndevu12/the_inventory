"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "../context/auth-context";

export function AccountTenantContextCard() {
  const { tenantSlug, memberships } = useAuth();
  const current = memberships.find((m) => m.tenant__slug === tenantSlug);

  if (!current) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current workspace</CardTitle>
          <CardDescription>
            Select an organisation from the switcher in the header to work in
            inventory.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Current workspace</CardTitle>
        <CardDescription>
          Inventory data and actions are scoped to this organisation.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <div>
          <p className="text-muted-foreground">Organisation</p>
          <p className="font-medium">{current.tenant__name}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Slug</p>
          <p className="font-mono text-xs">{current.tenant__slug}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Your role</p>
          <p className="font-medium capitalize">{current.role}</p>
        </div>
      </CardContent>
    </Card>
  );
}
