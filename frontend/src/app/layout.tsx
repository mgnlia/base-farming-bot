import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Base Farming Bot',
  description: 'Automated Base L2 airdrop farming dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen">{children}</body>
    </html>
  )
}
