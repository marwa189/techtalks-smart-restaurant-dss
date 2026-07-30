import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Restaurant Decision Support",
  description: "A responsive dashboard for restaurant operations and waste reduction insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
