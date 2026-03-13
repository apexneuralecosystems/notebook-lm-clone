'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { Brain, FileText, MessageSquare, Mic } from '@/components/LandingPageIcons';

// Landing page - explicitly prevents any redirects to /app or /login
// This ensures the root path (/) always shows the landing page
export default function Home() {
  const hasRun = useRef(false);

  // Explicitly prevent any redirects from landing page (run only once)
  useEffect(() => {
    // Only run once on mount
    if (hasRun.current || typeof window === 'undefined') return;
    hasRun.current = true;

    // CRITICAL: If we're on /app, redirect to / (should never happen, but safety check)
    if (window.location.pathname === '/app') {
      window.location.replace('/');
      return;
    }

    // Ensure we're on the root path
    if (window.location.pathname !== '/') {
      window.history.replaceState(null, '', '/');
    }
    
    // Clear any hash that might cause issues
    if (window.location.hash) {
      window.history.replaceState(null, '', '/');
    }
  }, []); // Empty dependency array - only run once

  // CRITICAL: Don't render if we're somehow on /app (should never happen)
  if (typeof window !== 'undefined' && window.location.pathname === '/app') {
    return null; // Will redirect via useEffect
  }

  // Landing page - always public, no authentication checks, no redirects
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="text-primary" size={32} />
            <h1 className="text-2xl font-bold">NotebookLM</h1>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="px-4 py-2 text-gray-300 hover:text-foreground transition-colors"
            >
              Login
            </Link>
            <Link
              href="/signup"
              className="px-6 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors font-semibold"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-5xl font-bold mb-6">
            Understand Anything with{' '}
            <span className="text-primary">AI-Powered</span> Insights
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
            Upload documents, websites, videos, or text. Get accurate, cited answers powered by your sources.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/signup"
              className="px-8 py-3 bg-primary hover:bg-primary-hover rounded-lg transition-colors font-semibold text-lg"
            >
              Start Free
            </Link>
            <Link
              href="/login"
              className="px-8 py-3 bg-secondary hover:bg-secondary-light rounded-lg transition-colors font-semibold text-lg border border-gray-700"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-secondary rounded-lg p-6 border border-gray-800">
            <div className="bg-primary/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <FileText className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Upload Sources</h3>
            <p className="text-gray-400">
              Add PDFs, websites, YouTube videos, audio files, or paste text directly. Your knowledge base, your way.
            </p>
          </div>

          <div className="bg-secondary rounded-lg p-6 border border-gray-800">
            <div className="bg-primary/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <MessageSquare className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Ask Questions</h3>
            <p className="text-gray-400">
              Get accurate answers with citations. Every response is grounded in your uploaded sources.
            </p>
          </div>

          <div className="bg-secondary rounded-lg p-6 border border-gray-800">
            <div className="bg-primary/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Mic className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-semibold mb-2">Generate Podcasts</h3>
            <p className="text-gray-400">
              Transform your sources into engaging podcast scripts with AI-generated dialogue and audio.
            </p>
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-20">
          <h3 className="text-3xl font-bold text-center mb-12">How It Works</h3>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-primary/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h4 className="font-semibold mb-2">Upload Sources</h4>
              <p className="text-sm text-gray-400">Add your documents, links, or text</p>
            </div>
            <div className="text-center">
              <div className="bg-primary/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h4 className="font-semibold mb-2">AI Processing</h4>
              <p className="text-sm text-gray-400">We analyze and index your content</p>
            </div>
            <div className="text-center">
              <div className="bg-primary/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h4 className="font-semibold mb-2">Ask Questions</h4>
              <p className="text-sm text-gray-400">Get answers with accurate citations</p>
            </div>
            <div className="text-center">
              <div className="bg-primary/20 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">4</span>
              </div>
              <h4 className="font-semibold mb-2">Create Content</h4>
              <p className="text-sm text-gray-400">Generate podcasts from your sources</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center space-y-2">
            <p className="text-gray-400">
              © {new Date().getFullYear()} Apex neural. All rights reserved.
            </p>
            <div className="flex items-center justify-center gap-2 text-gray-400">
              <Link href="/privacy" className="hover:text-foreground transition-colors">
                Privacy Policy
              </Link>
              <span>|</span>
              <Link href="/terms" className="hover:text-foreground transition-colors">
                Terms and Conditions
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
