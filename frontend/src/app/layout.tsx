/*
DIRECTION CONTRACT — Mid-century Educational
Seed key: 42ccc35a

THESIS: SkillSwap looks like opening a beautifully illustrated 1960s textbook —
warm, clear, optimistic about learning. Refuses the generic SaaS hero-features-
testimonials template and cold tech aesthetic. The visitor browses skills like
chapters, discovers mentors as illustrated guides.

OWN-WORLD: Warm cream ground (#F7F3ED). Accent palette: terracotta (#C4583F),
olive (#6B8E5F), golden (#D4A84B), soft teal (#5B8A8A). Slab serif display type
(Bitter), humanist sans body (Source Sans 3). Generous margins, clear hierarchy.
Diagrammatic SVG illustrations, friendly rounded shapes. Light mode only — this
is a daytime learning environment.

STORY: Visitor arrives seeking growth, sees warm invitation not sales pitch,
browses topics like textbook chapters, discovers mentors as knowledgeable guides,
feels invited to learn rather than pressured to convert.

FIRST VIEWPORT: Cream ground with friendly slab-serif headline, simple SVG
diagram showing skill-mentor connection, topic cards as color-coded sections
below. No stock photos. No hero image. Typography and illustration carry the
weight.

FORM: Mid-century educational, position 7 on grounded list, seed key 42ccc35a.
*/

import type { Metadata } from "next";
import { Bitter, Source_Sans_3 } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-provider";

const bitter = Bitter({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const sourceSans = Source_Sans_3({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "SkillSwap",
  description: "Connect with mentors and grow your skills",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${bitter.variable} ${sourceSans.variable} h-full`}
    >
      <body className="min-h-full flex flex-col bg-cream text-ink antialiased">
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
