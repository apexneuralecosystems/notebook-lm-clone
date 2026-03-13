'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useStore } from '@/lib/store';
import { authAPI } from '@/lib/api-client';
import SourcesSidebar from '@/components/SourcesSidebar';
import ChatInterface from '@/components/ChatInterface';
import StudioTab from '@/components/StudioTab';
import SourceUpload from '@/components/SourceUpload';
import { Loader2 } from 'lucide-react';

export default function AppPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, logout, accessToken, setAuth } = useStore();
  const [activeTab, setActiveTab] = useState<'sources' | 'chat' | 'studio'>('chat');
  const [isHydrated, setIsHydrated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // CRITICAL: Ensure app page only renders on /app, never on /
  // If somehow this component is rendered on root path, immediately redirect
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      if (currentPath === '/' || currentPath !== '/app') {
        // If we're not on /app, we shouldn't be here - redirect to landing page
        if (currentPath === '/') {
          // Force a full page reload to landing page
          window.location.replace('/');
          return;
        }
        // If on some other path that's not /app, redirect to /app
        if (currentPath !== '/app') {
          window.location.replace('/app');
          return;
        }
      }
    }
  }, [pathname]);
  
  // Don't render anything if we're on the wrong path
  if (typeof window !== 'undefined' && window.location.pathname !== '/app') {
    return null;
  }

  // Wait for Zustand persist to hydrate from localStorage
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Restore user data if token exists but user data is missing
  useEffect(() => {
    if (!isHydrated) return;
    
    const token = accessToken || (typeof window !== 'undefined' ? localStorage.getItem('access_token') : null);
    
    if (!token) {
      setIsCheckingAuth(false);
      router.push('/login');
      return;
    }
    
    // If we have a token but no user data, try to fetch it
    if (token && !user) {
      authAPI.getCurrentUser()
        .then((response) => {
          if (response.status && response.data) {
            const userData = response.data;
            const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
            setAuth(
              {
                id: userData.user_id,
                email: userData.email,
                full_name: userData.full_name || undefined,
                username: userData.username || undefined,
              },
              token,
              refreshToken
            );
          }
          setIsCheckingAuth(false);
        })
        .catch(() => {
          // Token might be invalid, redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
          }
          setIsCheckingAuth(false);
          router.push('/login');
        });
    } else {
      setIsCheckingAuth(false);
    }
  }, [isHydrated, accessToken, user, setAuth, router]);

  // Show loading while checking authentication
  if (!isHydrated || isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 size={32} className="mx-auto mb-4 text-primary animate-spin" />
          <h1 className="text-xl font-bold">Loading...</h1>
        </div>
      </div>
    );
  }

  // Check authentication after hydration and auth check
  const hasToken = isAuthenticated || (typeof window !== 'undefined' && localStorage.getItem('access_token'));
  if (!hasToken) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sources Sidebar */}
      <SourcesSidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-secondary border-b border-gray-700 px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">🧠 NotebookLM: Understand Anything</h1>
          <div className="flex items-center gap-4">
            {user && (
              <div className="text-sm text-gray-400">
                {user.email}
              </div>
            )}
            <button
              onClick={() => {
                logout();
                router.push('/login');
              }}
              className="px-4 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Tabs */}
        <div className="border-b border-gray-700">
          <div className="flex">
            <button
              onClick={() => setActiveTab('sources')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'sources'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-gray-400 hover:text-foreground'
              }`}
            >
              📁 Add Sources
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-gray-400 hover:text-foreground'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveTab('studio')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'studio'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-gray-400 hover:text-foreground'
              }`}
            >
              🎙️ Studio
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-auto">
          {activeTab === 'sources' && <SourceUpload />}
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'studio' && <StudioTab />}
        </div>
      </div>
    </div>
  );
}

