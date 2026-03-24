import { z } from "zod";

export function createLoginSchema(msgs: {
  usernameRequired: string;
  passwordRequired: string;
}) {
  return z.object({
    username: z
      .string()
      .min(1, msgs.usernameRequired)
      .transform((v) => v.trim()),
    password: z.string().min(1, msgs.passwordRequired),
  });
}

export type LoginFormValues = z.infer<ReturnType<typeof createLoginSchema>>;

export function createProfileSchema(msgs: {
  emailRequired: string;
  validEmail: string;
}) {
  return z.object({
    email: z
      .string()
      .min(1, msgs.emailRequired)
      .email(msgs.validEmail),
    first_name: z.string(),
    last_name: z.string(),
  });
}

export type ProfileFormValues = z.infer<ReturnType<typeof createProfileSchema>>;

export function createChangePasswordSchema(msgs: {
  currentRequired: string;
  newMin: string;
  confirmRequired: string;
  mismatch: string;
}) {
  return z
    .object({
      old_password: z.string().min(1, msgs.currentRequired),
      new_password: z.string().min(8, msgs.newMin),
      confirm_password: z.string().min(1, msgs.confirmRequired),
    })
    .refine((data) => data.new_password === data.confirm_password, {
      message: msgs.mismatch,
      path: ["confirm_password"],
    });
}

export type ChangePasswordFormValues = z.infer<
  ReturnType<typeof createChangePasswordSchema>
>;

export function createRegisterSchema(msgs: {
  organizationNameRequired: string;
  slugFormat: string;
  usernameRequired: string;
  validEmail: string;
  passwordMin: string;
}) {
  return z.object({
    organization_name: z.string().min(1, msgs.organizationNameRequired),
    organization_slug: z
      .string()
      .optional()
      .refine(
        (v) => !v || /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(v),
        msgs.slugFormat,
      ),
    owner_username: z.string().min(1, msgs.usernameRequired),
    owner_email: z.string().email(msgs.validEmail),
    owner_password: z.string().min(8, msgs.passwordMin),
    owner_first_name: z.string().optional(),
    owner_last_name: z.string().optional(),
  });
}

export type RegisterFormValues = z.infer<ReturnType<typeof createRegisterSchema>>;
