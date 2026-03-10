import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'TrendIt',
  description: 'Virtual investing with explainable AI analysis',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav>
          <a href="/">Dashboard</a>
          <a href="/research">Ticker Research</a>
        </nav>
        {children}
      </body>
    </html>
  );
}
