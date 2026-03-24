import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(1, "Username is required").transform((v) => v.trim()),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const profileSchema = z.object({
  email: z.string().min(1, "Email is required").email("Valid email is required"),
  first_name: z.string(),
  last_name: z.string(),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;

export const changePasswordSchema = z
  .object({
    old_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "New password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your new password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

export const registerSchema = z.object({
  organization_name: z.string().min(1, "Organization name is required"),
  organization_slug: z
    .string()
    .optional()
    .refine(
      (v) => !v || /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v),
      "Slug must be lowercase letters, numbers, and hyphens only"
    ),
  owner_username: z.string().min(1, "Username is required"),
  owner_email: z.string().email("Valid email is required"),
  owner_password: z.string().min(8, "Password must be at least 8 characters"),
  owner_first_name: z.string().optional(),
  owner_last_name: z.string().optional(),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
