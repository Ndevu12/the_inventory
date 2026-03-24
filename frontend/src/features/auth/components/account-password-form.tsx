"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createChangePasswordSchema,
  type ChangePasswordFormValues,
} from "../helpers/auth-schemas";
import { useChangePassword } from "../hooks/use-auth";

export function AccountPasswordForm() {
  const t = useTranslations("Auth.account");
  const tVal = useTranslations("Auth.validation");
  const changePassword = useChangePassword();

  const schema = React.useMemo(
    () =>
      createChangePasswordSchema({
        currentRequired: tVal("currentPasswordRequired"),
        newMin: tVal("newPasswordMin"),
        confirmRequired: tVal("confirmPasswordRequired"),
        mismatch: tVal("passwordsMismatch"),
      }),
    [tVal],
  );

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      old_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  function onSubmit(values: ChangePasswordFormValues) {
    changePassword.mutate(
      {
        old_password: values.old_password,
        new_password: values.new_password,
      },
      {
        onSuccess: () => {
          reset({
            old_password: "",
            new_password: "",
            confirm_password: "",
          });
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t("passwordTitle")}</CardTitle>
        <CardDescription>{t("passwordDescription")}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="account-old-password">{t("currentPassword")}</Label>
            <Input
              id="account-old-password"
              type="password"
              autoComplete="current-password"
              disabled={changePassword.isPending}
              aria-invalid={!!errors.old_password}
              {...register("old_password")}
            />
            {errors.old_password && (
              <p className="text-xs text-destructive">
                {errors.old_password.message}
              </p>
            )}
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account-new-password">{t("newPassword")}</Label>
            <Input
              id="account-new-password"
              type="password"
              autoComplete="new-password"
              disabled={changePassword.isPending}
              aria-invalid={!!errors.new_password}
              {...register("new_password")}
            />
            {errors.new_password && (
              <p className="text-xs text-destructive">
                {errors.new_password.message}
              </p>
            )}
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account-confirm-password">
              {t("confirmPassword")}
            </Label>
            <Input
              id="account-confirm-password"
              type="password"
              autoComplete="new-password"
              disabled={changePassword.isPending}
              aria-invalid={!!errors.confirm_password}
              {...register("confirm_password")}
            />
            {errors.confirm_password && (
              <p className="text-xs text-destructive">
                {errors.confirm_password.message}
              </p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" disabled={changePassword.isPending}>
            {changePassword.isPending ? t("updatingPassword") : t("updatePassword")}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
