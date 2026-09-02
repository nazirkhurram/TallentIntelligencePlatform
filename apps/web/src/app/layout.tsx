import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "ENUM Talent Intelligence Platform",
  description: "AI-native talent platform on self-hosted infrastructure",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
