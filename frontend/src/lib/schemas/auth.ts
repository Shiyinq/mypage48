import { z } from 'zod';

// Login Schema
export const loginSchema = z.object({
	email: z.string().email({ message: 'Invalid email address' }),
	password: z.string().min(1, { message: 'Password is required' })
});

// Register Schema
export const registerSchema = z
	.object({
		memberId: z
			.string()
			.regex(/^JKT-\d{4}$/, { message: 'Member ID must be in format JKT-XXXX (e.g. JKT-1234)' }),
		username: z
			.string()
			.min(3, { message: 'Username must be at least 3 characters' })
			.max(20, { message: 'Username must be at most 20 characters' })
			.regex(/^[a-zA-Z0-9_]+$/, {
				message: 'Username can only contain letters, numbers, and underscores'
			}),
		fullName: z.string().min(2, { message: 'Full name must be at least 2 characters' }),
		email: z.string().email({ message: 'Invalid email address' }),
		ofcStatus: z.enum(['Active', 'Inactive', 'Pending']),
		password: z
			.string()
			.min(8, { message: 'Password must be at least 8 characters' })
			.regex(/[A-Z]/, { message: 'Password must contain at least one uppercase letter' })
			.regex(/[0-9]/, { message: 'Password must contain at least one number' }),
		confirmPassword: z.string()
	})
	.refine((data) => data.password === data.confirmPassword, {
		message: "Passwords don't match",
		path: ['confirmPassword']
	});

export type LoginSchema = z.infer<typeof loginSchema>;
export type RegisterSchema = z.infer<typeof registerSchema>;
