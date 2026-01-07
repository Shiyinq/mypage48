import { dev } from '$app/environment';
import { showToast } from '$lib/stores/toast';

type LogLevel = 'info' | 'warn' | 'error';

interface LogOptions {
	context?: string;
	showToast?: boolean;
	toastMessage?: string;
}

class Logger {
	private log(level: LogLevel, message: string, error?: unknown, options?: LogOptions) {
		const context = options?.context ? `[${options.context}]` : '';
		const timestamp = new Date().toISOString();

		// In development, log everything to console
		if (dev) {
			const consoleMethod =
				level === 'info' ? console.log : level === 'warn' ? console.warn : console.error;
			consoleMethod(`${timestamp} ${level.toUpperCase()} ${context} ${message}`, error || '');
		} else {
			// In production, we would send this to a monitoring service (Sentry, LogRocket, etc.)
			// For now, we only log errors to console to avoid leaking sensitive info
			if (level === 'error') {
				// console.error(`${timestamp} ${context} ${message}`); // Uncomment if you want production logs
			}
		}

		// User feedback if requested
		if (options?.showToast) {
			const toastType = level === 'error' ? 'error' : 'success';
			const toastMsg =
				options.toastMessage || (level === 'error' ? 'An unexpected error occurred' : message);
			showToast(toastMsg, toastType);
		}
	}

	info(message: string, options?: LogOptions) {
		this.log('info', message, undefined, options);
	}

	warn(message: string, error?: unknown, options?: LogOptions) {
		this.log('warn', message, error, options);
	}

	error(message: string, error?: unknown, options?: LogOptions) {
		this.log('error', message, error, options);
	}
}

export const logger = new Logger();
