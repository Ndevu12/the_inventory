"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Package, Box, AlertCircle, Search, Zap } from "lucide-react";

import { useAuth } from "../context/auth-context";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoginForm } from "../components/login-form";
import { FeatureCard } from "../components/feature-card";
import { FeaturesList } from "../components/feature-list";
import { useLogin, useAuthConfig } from "../hooks/use-auth";
import { useLoginFormStore } from "../stores/login-form-store";
import type { LoginFormValues } from "../helpers/auth-schemas";

function LoginPageRegisterLink() {
  const { data: config } = useAuthConfig();
  if (!config?.allow_registration) return null;
  return (
    <p className="text-center text-sm text-muted-foreground">
      Don&apos;t have an organization?{" "}
      <Link
        href="/register"
        className="text-primary underline hover:no-underline"
      >
        Create one
      </Link>
    </p>
  );
}

export function LoginPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { isReady, isAuthenticated } = useAuth();
  const loginMutation = useLogin();
  const { serverError, setServerError, reset } = useLoginFormStore();

  useEffect(() => {
    if (!isReady) return;
    if (pathname !== "/login") return;
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isReady, isAuthenticated, pathname, router]);

  useEffect(() => {
    return () => reset();
  }, [reset]);

  function handleSubmit(values: LoginFormValues) {
    setServerError(null);
    loginMutation.mutate(values, {
      onError: (error) => {
        const message =
          (error as { message?: string }).message ??
          "Invalid username or password";
        setServerError(message);
      },
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl grid grid-cols-1 gap-8 md:grid-cols-2 items-center">
        {/* Left side: Login Form */}
        <div>
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <Package className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">Welcome back</CardTitle>
              <CardDescription>
                Sign in to The Inventory
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <LoginForm
                onSubmit={handleSubmit}
                isPending={loginMutation.isPending}
                serverError={serverError}
              />
              <LoginPageRegisterLink />
            </CardContent>
          </Card>
        </div>

        {/* Right side: Features */}
        <div className="hidden md:block">
          <FeaturesList
            title="Powerful Inventory Management"
            subtitle="Everything you need to manage inventory efficiently"
          >
            <FeatureCard
              icon={Box}
              title="Catalog Management"
              description="Organize products with SKUs, descriptions, images, and hierarchical categories"
            />
            <FeatureCard
              icon={Zap}
              title="Real-time Tracking"
              description="Track stock movements across multiple warehouses with instant updates"
            />
            <FeatureCard
              icon={AlertCircle}
              title="Smart Alerts"
              description="Set reorder points and receive instant notifications when stock runs low"
            />
            <FeatureCard
              icon={Search}
              title="Advanced Search"
              description="Find products, categories, and locations with powerful full-text search"
            />
          </FeaturesList>
        </div>
      </div>
    </div>
  );
}
