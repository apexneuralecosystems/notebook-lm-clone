/**
 * Centralized environment variable access for Next.js App Router
 * 
 * - Server-side: Reads from process.env
 * - Client-side: Reads from window.__ENV__ (injected via /env.js)
 * 
 * This allows runtime environment variable injection without rebuilding the Docker image.
 */

// Type definition for window.__ENV__
declare global {
  interface Window {
    __ENV__?: {
      NEXT_PUBLIC_API_URL?: string;
    };
  }
}

/**
 * Get environment variable value
 * Safe for use in both server and client components
 */
export function getEnv(key: 'NEXT_PUBLIC_API_URL'): string | undefined {
  // Server-side: read from process.env
  if (typeof window === 'undefined') {
    return process.env[key];
  }

  // Client-side: read from window.__ENV__ (injected via /env.js)
  return window.__ENV__?.[key];
}

/**
 * Get NEXT_PUBLIC_API_URL with validation
 * Throws error if not set (only in browser, not during SSR)
 */
export function getApiUrl(): string {
  const apiUrl = getEnv('NEXT_PUBLIC_API_URL');

  // Only validate in browser (not during SSR)
  if (typeof window !== 'undefined' && !apiUrl) {
    console.error('⚠️ NEXT_PUBLIC_API_URL is not configured');
    console.error('⚠️ Make sure /env.js is loaded and NEXT_PUBLIC_API_URL is set in Dokploy Environments');
    throw new Error('NEXT_PUBLIC_API_URL is not set. Check /env.js and Dokploy environment variables.');
  }

  return apiUrl || '';
}

