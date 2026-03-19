"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Package } from "lucide-react";

import { useAuth } from "../context/auth-context";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoginForm } from "../components/login-form";
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
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
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
  );
}
