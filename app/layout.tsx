import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PRISM — Code Review Assistant',
  description: 'Review code for security, quality, and performance issues with PRISM.',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: './icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: './icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: './icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: './apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#080d15',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
