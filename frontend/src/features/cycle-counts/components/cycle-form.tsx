"use client";

import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  createCycleSchema,
  type CreateCycleFormValues,
} from "../helpers/cycle-schemas";
import type { CycleCreatePayload } from "../types/cycle-count.types";

interface LocationOption {
  id: number;
  name: string;
}

interface CycleFormProps {
  locations: LocationOption[];
  onSubmit: (values: CycleCreatePayload) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function CycleForm({
  locations,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: CycleFormProps) {
  const t = useTranslations("CycleCounts.form");
  const tVal = useTranslations("CycleCounts.form.validation");
  const tCommon = useTranslations("Common.actions");

  const schema = useMemo(
    () =>
      createCycleSchema({
        nameRequired: tVal("nameRequired"),
        scheduledRequired: tVal("scheduledRequired"),
      }),
    [tVal],
  );

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateCycleFormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      location: "",
      scheduled_date: new Date().toISOString().split("T")[0],
      notes: "",
    },
  });

  function handleFormSubmit(values: CreateCycleFormValues) {
    onSubmit({
      name: values.name,
      location: values.location ? Number(values.location) : null,
      scheduled_date: values.scheduled_date,
      notes: values.notes,
    });
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)}>
      <Card>
        <CardHeader>
          <CardTitle>{t("cardTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">{t("name")}</Label>
              <Input
                id="name"
                placeholder={t("namePlaceholder")}
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>{t("locationOptional")}</Label>
              <Select
                value={watch("location") || ""}
                onValueChange={(val) => {
                  if (val) {
                    const locationValue = val === "__all__" ? "" : val;
                    setValue("location", locationValue, {
                      shouldValidate: true,
                    });
                  }
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("allLocationsPlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">
                    {t("allLocationsOption")}
                  </SelectItem>
                  {locations.map((l) => (
                    <SelectItem key={l.id} value={l.id.toString()}>
                      {l.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="scheduled_date">{t("scheduledDate")}</Label>
              <Input
                id="scheduled_date"
                type="date"
                {...register("scheduled_date")}
              />
              {errors.scheduled_date && (
                <p className="text-xs text-destructive">
                  {errors.scheduled_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">{t("notesOptional")}</Label>
            <Textarea
              id="notes"
              rows={3}
              placeholder={t("notesPlaceholder")}
              {...register("notes")}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            {tCommon("cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t("submitting") : t("submit")}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
