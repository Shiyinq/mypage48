import { z } from 'zod';

// Login Schema
export const loginSchema = z.object({
	email: z.string().min(3, { message: 'Email or Username must be at least 3 characters' }),
	password: z.string().min(1, { message: 'Password is required' })
});

// Register Schema
export const registerBaseSchema = z.object({
	username: z
		.string()
		.min(3, { message: 'Username must be at least 3 characters' })
		.max(20, { message: 'Username must be at most 20 characters' })
		.regex(/^[a-zA-Z0-9_]+$/, {
			message: 'Username can only contain letters, numbers, and underscores'
		}),
	fullName: z.string().min(2, { message: 'Full name must be at least 2 characters' }),
	email: z.string().email({ message: 'Invalid email address' }),
	password: z
		.string()
		.min(8, { message: 'Password must be at least 8 characters' })
		.max(128, { message: 'Password must be at most 128 characters' })
		.regex(/[A-Z]/, { message: 'Password must contain at least one uppercase letter' })
		.regex(/[a-z]/, { message: 'Password must contain at least one lowercase letter' })
		.regex(/[0-9]/, { message: 'Password must contain at least one number' })
		.regex(/[^A-Za-z0-9]/, { message: 'Password must contain at least one symbol' })
		.regex(/^\S*$/, { message: 'Password must not contain spaces' }),
	confirmPassword: z.string()
});

export const registerSchema = registerBaseSchema.refine(
	(data) => data.password === data.confirmPassword,
	{
		message: "Passwords don't match",
		path: ['confirmPassword']
	}
);

export type LoginSchema = z.infer<typeof loginSchema>;
export type RegisterSchema = z.infer<typeof registerSchema>;

// Forgot Password Schema
export const forgotPasswordSchema = z.object({
	email: z.string().email({ message: 'Invalid email address' })
});

// Reset Password Schema
export const resetPasswordBaseSchema = z.object({
	newPassword: z
		.string()
		.min(8, { message: 'Password must be at least 8 characters' })
		.max(128, { message: 'Password must be at most 128 characters' })
		.regex(/[A-Z]/, { message: 'Password must contain at least one uppercase letter' })
		.regex(/[a-z]/, { message: 'Password must contain at least one lowercase letter' })
		.regex(/[0-9]/, { message: 'Password must contain at least one number' })
		.regex(/[^A-Za-z0-9]/, { message: 'Password must contain at least one symbol' })
		.regex(/^\S*$/, { message: 'Password must not contain spaces' }),
	confirmPassword: z.string()
});

export const resetPasswordSchema = resetPasswordBaseSchema.refine(
	(data) => data.newPassword === data.confirmPassword,
	{
		message: "Passwords don't match",
		path: ['confirmPassword']
	}
);

export type ForgotPasswordSchema = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordSchema = z.infer<typeof resetPasswordSchema>;
