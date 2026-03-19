import type { CycleStatus, VarianceType, VarianceResolution } from "../types/cycle-count.types";

export const CYCLE_STATUSES: {
  value: CycleStatus;
  label: string;
}[] = [
  { value: "scheduled", label: "Scheduled" },
  { value: "in_progress", label: "In Progress" },
  { value: "completed", label: "Completed" },
  { value: "reconciled", label: "Reconciled" },
];

export const CYCLE_STATUS_COLOR_MAP: Record<
  CycleStatus,
  { bg: string; text: string }
> = {
  scheduled: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-800 dark:text-blue-300" },
  in_progress: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-800 dark:text-yellow-300" },
  completed: { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-800 dark:text-orange-300" },
  reconciled: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
};

export const VARIANCE_TYPE_COLOR_MAP: Record<
  VarianceType,
  { bg: string; text: string }
> = {
  shortage: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-300" },
  surplus: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-800 dark:text-blue-300" },
  match: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
};

export const RESOLUTION_OPTIONS: {
  value: VarianceResolution;
  label: string;
}[] = [
  { value: "accepted", label: "Accept (Create Adjustment)" },
  { value: "investigating", label: "Investigate" },
  { value: "rejected", label: "Reject (No Change)" },
];

export const RESOLUTION_COLOR_MAP: Record<
  VarianceResolution,
  { bg: string; text: string }
> = {
  accepted: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-800 dark:text-green-300" },
  investigating: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-800 dark:text-yellow-300" },
  rejected: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-800 dark:text-red-300" },
};
