"use client";

import * as React from "react";
import { Link, useRouter } from "@/i18n/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Package, Loader2, Box, AlertCircle, Search, Zap } from "lucide-react";
import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FeatureCard } from "../components/feature-card";
import { FeaturesList } from "../components/feature-list";
import {
  createRegisterSchema,
  type RegisterFormValues,
} from "../helpers/auth-schemas";
import { useAuthConfig, useRegister } from "../hooks/use-auth";

export function RegisterCompanyPage() {
  const router = useRouter();
  const t = useTranslations("Auth");
  const tReg = useTranslations("Auth.register");
  const tVal = useTranslations("Auth.validation");
  const tMarketing = useTranslations("Auth.marketing");
  const { data: config, isLoading: configLoading } = useAuthConfig();
  const registerMutation = useRegister();

  const schema = React.useMemo(
    () =>
      createRegisterSchema({
        organizationNameRequired: tVal("organizationNameRequired"),
        slugFormat: tVal("slugFormat"),
        usernameRequired: tVal("usernameRequired"),
        validEmail: tVal("validEmail"),
        passwordMin: tVal("registerPasswordMin"),
      }),
    [tVal],
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      organization_name: "",
      organization_slug: "",
      owner_username: "",
      owner_email: "",
      owner_password: "",
      owner_first_name: "",
      owner_last_name: "",
    },
  });

  React.useEffect(() => {
    if (!configLoading && config && !config.allow_registration) {
      router.replace("/login");
    }
  }, [config, configLoading, router]);

  function onSubmit(values: RegisterFormValues) {
    const payload = {
      organization_name: values.organization_name.trim(),
      owner_username: values.owner_username.trim(),
      owner_email: values.owner_email.trim().toLowerCase(),
      owner_password: values.owner_password,
      owner_first_name: values.owner_first_name?.trim() || "",
      owner_last_name: values.owner_last_name?.trim() || "",
    };
    if (values.organization_slug?.trim()) {
      (payload as Record<string, unknown>).organization_slug =
        values.organization_slug.trim();
    }
    registerMutation.mutate(payload, {
      onError: (error) => {
        const msg =
          (error as { message?: string }).message ?? t("registrationFailed");
        toast.error(msg);
      },
    });
  }

  if (configLoading || (!config?.allow_registration && !configLoading)) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center gap-4 py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">{t("loading")}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl grid grid-cols-1 gap-8 md:grid-cols-2 items-start">
        <div>
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <Package className="h-6 w-6 text-primary" />
              </div>
              <CardTitle className="text-xl">{tReg("title")}</CardTitle>
              <CardDescription>{tReg("description")}</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="organization_name">{tReg("organizationName")}</Label>
                  <Input
                    id="organization_name"
                    placeholder={tReg("organizationPlaceholder")}
                    autoComplete="organization"
                    disabled={registerMutation.isPending}
                    {...register("organization_name")}
                  />
                  {errors.organization_name && (
                    <p className="text-xs text-destructive">
                      {errors.organization_name.message}
                    </p>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="organization_slug">
                    {tReg("slugLabel")}
                    <span className="ml-1 font-normal text-muted-foreground">
                      {tReg("slugHint")}
                    </span>
                  </Label>
                  <Input
                    id="organization_slug"
                    placeholder={tReg("slugPlaceholder")}
                    disabled={registerMutation.isPending}
                    {...register("organization_slug")}
                  />
                  {errors.organization_slug && (
                    <p className="text-xs text-destructive">
                      {errors.organization_slug.message}
                    </p>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="owner_username">{tReg("username")}</Label>
                  <Input
                    id="owner_username"
                    placeholder={tReg("usernamePlaceholder")}
                    autoComplete="username"
                    disabled={registerMutation.isPending}
                    {...register("owner_username")}
                  />
                  {errors.owner_username && (
                    <p className="text-xs text-destructive">
                      {errors.owner_username.message}
                    </p>
                  )}
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="owner_email">{tReg("email")}</Label>
                  <Input
                    id="owner_email"
                    type="email"
                    placeholder={tReg("emailPlaceholder")}
                    autoComplete="email"
                    disabled={registerMutation.isPending}
                    {...register("owner_email")}
                  />
                  {errors.owner_email && (
                    <p className="text-xs text-destructive">
                      {errors.owner_email.message}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="owner_first_name">{tReg("firstName")}</Label>
                    <Input
                      id="owner_first_name"
                      placeholder={tReg("firstNamePlaceholder")}
                      disabled={registerMutation.isPending}
                      {...register("owner_first_name")}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="owner_last_name">{tReg("lastName")}</Label>
                    <Input
                      id="owner_last_name"
                      placeholder={tReg("lastNamePlaceholder")}
                      disabled={registerMutation.isPending}
                      {...register("owner_last_name")}
                    />
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="owner_password">{tReg("password")}</Label>
                  <Input
                    id="owner_password"
                    type="password"
                    placeholder={tReg("passwordPlaceholder")}
                    autoComplete="new-password"
                    disabled={registerMutation.isPending}
                    {...register("owner_password")}
                  />
                  {errors.owner_password && (
                    <p className="text-xs text-destructive">
                      {errors.owner_password.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  size="lg"
                  className="w-full"
                  disabled={registerMutation.isPending}
                >
                  {registerMutation.isPending && (
                    <Loader2 className="mr-2 size-4 animate-spin" />
                  )}
                  {registerMutation.isPending ? tReg("submitting") : tReg("submit")}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  {tReg("hasAccountPrompt")}{" "}
                  <Link
                    href="/login"
                    className="text-primary underline hover:no-underline"
                  >
                    {tReg("signInLink")}
                  </Link>
                </p>
              </form>
            </CardContent>
          </Card>
        </div>

        <div className="hidden md:block">
          <FeaturesList
            title={tMarketing("title")}
            subtitle={tMarketing("subtitle")}
          >
            <FeatureCard
              icon={Box}
              title={tMarketing("catalogTitle")}
              description={tMarketing("catalogDescription")}
            />
            <FeatureCard
              icon={Zap}
              title={tMarketing("trackingTitle")}
              description={tMarketing("trackingDescription")}
            />
            <FeatureCard
              icon={AlertCircle}
              title={tMarketing("alertsTitle")}
              description={tMarketing("alertsDescription")}
            />
            <FeatureCard
              icon={Search}
              title={tMarketing("searchTitle")}
              description={tMarketing("searchDescription")}
            />
          </FeaturesList>
        </div>
      </div>
    </div>
  );
}
