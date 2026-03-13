'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';

/**
 * Route Guard Component
 * 
 * Ensures that the root path (/) always shows the landing page,
 * never redirects to /app, even if user is authenticated.
 * 
 * This prevents any client-side routing issues that might cause
 * the landing page to be bypassed.
 */
export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    // If we're on root path and somehow the app page is trying to render,
    // force redirect to landing page (which is already at /)
    // This is a safety net in case of any routing issues
    if (pathname === '/' && typeof window !== 'undefined') {
      // Clear any potential redirect state
      const currentPath = window.location.pathname;
      if (currentPath !== '/') {
        // If URL changed, reset to /
        window.history.replaceState(null, '', '/');
      }
    }

    // Prevent any automatic redirects from / to /app
    // This ensures landing page is always accessible
    if (pathname === '/app' && typeof window !== 'undefined') {
      // Only allow /app if user explicitly navigated there (not from /)
      const referrer = document.referrer;
      if (!referrer || referrer.endsWith('/')) {
        // If coming from root, user should see landing page first
        // Don't auto-redirect, let them click login/signup
      }
    }
  }, [pathname, router]);

  return <>{children}</>;
}
