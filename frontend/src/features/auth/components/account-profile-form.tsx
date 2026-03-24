"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

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
import type { User } from "@/lib/auth-store";
import { profileSchema, type ProfileFormValues } from "../helpers/auth-schemas";
import { useUpdateProfile } from "../hooks/use-auth";

interface AccountProfileFormProps {
  user: User;
}

export function AccountProfileForm({ user }: AccountProfileFormProps) {
  const updateMutation = useUpdateProfile();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      email: user.email,
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
    },
  });

  React.useEffect(() => {
    reset({
      email: user.email,
      first_name: user.first_name ?? "",
      last_name: user.last_name ?? "",
    });
  }, [user, reset]);

  function onSubmit(values: ProfileFormValues) {
    updateMutation.mutate({
      email: values.email.trim().toLowerCase(),
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Profile</CardTitle>
        <CardDescription>
          Your name and email apply across every organisation you belong to.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="account-username">Username</Label>
            <Input
              id="account-username"
              value={user.username}
              disabled
              readOnly
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              Username cannot be changed here.
            </p>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="account-email">Email</Label>
            <Input
              id="account-email"
              type="email"
              autoComplete="email"
              disabled={updateMutation.isPending}
              aria-invalid={!!errors.email}
              {...register("email")}
            />
            {errors.email && (
              <p className="text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="account-first-name">First name</Label>
              <Input
                id="account-first-name"
                autoComplete="given-name"
                disabled={updateMutation.isPending}
                aria-invalid={!!errors.first_name}
                {...register("first_name")}
              />
              {errors.first_name && (
                <p className="text-xs text-destructive">
                  {errors.first_name.message}
                </p>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="account-last-name">Last name</Label>
              <Input
                id="account-last-name"
                autoComplete="family-name"
                disabled={updateMutation.isPending}
                aria-invalid={!!errors.last_name}
                {...register("last_name")}
              />
              {errors.last_name && (
                <p className="text-xs text-destructive">
                  {errors.last_name.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={updateMutation.isPending || !isDirty}
            onClick={() =>
              reset({
                email: user.email,
                first_name: user.first_name ?? "",
                last_name: user.last_name ?? "",
              })
            }
          >
            Reset
          </Button>
          <Button type="submit" disabled={updateMutation.isPending || !isDirty}>
            {updateMutation.isPending ? "Saving…" : "Save profile"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
