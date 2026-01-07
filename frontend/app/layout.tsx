import type { Metadata } from 'next'
import Script from 'next/script'
import './globals.css'

export const metadata: Metadata = {
  title: 'NotebookLM - Understand Anything',
  description: 'Document-grounded AI assistant with accurate citations',
  icons: {
    icon: '/icon.svg',
    shortcut: '/icon.svg',
    apple: '/icon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* Load runtime environment variables before React hydrates */}
        {/* This must load synchronously and before any client components */}
        <Script
          id="env-loader"
          strategy="beforeInteractive"
          src="/env.js"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}

