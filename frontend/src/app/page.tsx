"use client";

import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";
import { useTopics } from "@/hooks/use-topics";

// Color rotation for topic cards
const topicColors = [
  { bg: "bg-terracotta-light", border: "border-terracotta", text: "text-terracotta-dark" },
  { bg: "bg-olive-light", border: "border-olive", text: "text-olive-dark" },
  { bg: "bg-golden-light", border: "border-golden", text: "text-golden-dark" },
  { bg: "bg-teal-light", border: "border-teal", text: "text-teal-dark" },
];

// Simple SVG illustration component
function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 400 240"
      fill="none"
      className="w-full max-w-md mx-auto"
      aria-hidden="true"
    >
      {/* Connection lines */}
      <path
        d="M120 120 L200 80 L280 120"
        stroke="var(--golden)"
        strokeWidth="2"
        strokeDasharray="6 4"
        fill="none"
      />
      <path
        d="M120 120 L200 160 L280 120"
        stroke="var(--teal)"
        strokeWidth="2"
        strokeDasharray="6 4"
        fill="none"
      />

      {/* Left figure - the learner */}
      <circle cx="120" cy="120" r="32" fill="var(--terracotta-light)" />
      <circle cx="120" cy="108" r="12" fill="var(--terracotta)" />
      <path
        d="M108 124 Q120 140 132 124"
        stroke="var(--terracotta)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <text
        x="120"
        y="175"
        textAnchor="middle"
        className="fill-ink-muted"
        style={{ fontSize: "13px", fontFamily: "var(--font-body)" }}
      >
        You
      </text>

      {/* Center - the skill/topic */}
      <rect
        x="170"
        y="100"
        width="60"
        height="40"
        rx="6"
        fill="var(--golden-light)"
        stroke="var(--golden)"
        strokeWidth="2"
      />
      <text
        x="200"
        y="125"
        textAnchor="middle"
        className="fill-golden-dark"
        style={{ fontSize: "12px", fontWeight: 600, fontFamily: "var(--font-body)" }}
      >
        Skill
      </text>

      {/* Right figure - the mentor */}
      <circle cx="280" cy="120" r="32" fill="var(--olive-light)" />
      <circle cx="280" cy="108" r="12" fill="var(--olive)" />
      <path
        d="M268 124 Q280 140 292 124"
        stroke="var(--olive)"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      {/* Mentor indicator - small teaching element */}
      <rect x="295" y="95" width="16" height="20" rx="2" fill="var(--olive)" />
      <line x1="299" y1="100" x2="307" y2="100" stroke="var(--olive-light)" strokeWidth="2" />
      <line x1="299" y1="105" x2="305" y2="105" stroke="var(--olive-light)" strokeWidth="2" />
      <line x1="299" y1="110" x2="307" y2="110" stroke="var(--olive-light)" strokeWidth="2" />
      <text
        x="280"
        y="175"
        textAnchor="middle"
        className="fill-ink-muted"
        style={{ fontSize: "13px", fontFamily: "var(--font-body)" }}
      >
        Mentor
      </text>

      {/* Small decorative elements */}
      <circle cx="60" cy="60" r="4" fill="var(--terracotta)" opacity="0.4" />
      <circle cx="340" cy="60" r="4" fill="var(--olive)" opacity="0.4" />
      <circle cx="60" cy="180" r="3" fill="var(--teal)" opacity="0.4" />
      <circle cx="340" cy="180" r="3" fill="var(--golden)" opacity="0.4" />
    </svg>
  );
}

// Decorative corner element
function CornerDecoration({ position }: { position: "top-left" | "bottom-right" }) {
  const isTopLeft = position === "top-left";
  return (
    <svg
      className={`absolute ${isTopLeft ? "top-0 left-0" : "bottom-0 right-0"} w-24 h-24 pointer-events-none`}
      viewBox="0 0 100 100"
      fill="none"
      aria-hidden="true"
    >
      {isTopLeft ? (
        <>
          <circle cx="10" cy="10" r="3" fill="var(--terracotta)" opacity="0.3" />
          <circle cx="25" cy="15" r="2" fill="var(--golden)" opacity="0.3" />
          <line x1="5" y1="30" x2="30" y2="30" stroke="var(--cream-dark)" strokeWidth="1" />
          <line x1="5" y1="35" x2="20" y2="35" stroke="var(--cream-dark)" strokeWidth="1" />
        </>
      ) : (
        <>
          <circle cx="90" cy="90" r="3" fill="var(--olive)" opacity="0.3" />
          <circle cx="75" cy="85" r="2" fill="var(--teal)" opacity="0.3" />
          <line x1="70" y1="70" x2="95" y2="70" stroke="var(--cream-dark)" strokeWidth="1" />
          <line x1="80" y1="65" x2="95" y2="65" stroke="var(--cream-dark)" strokeWidth="1" />
        </>
      )}
    </svg>
  );
}

export default function Home() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: topicsData, isLoading: topicsLoading, error } = useTopics();

  return (
    <main className="flex flex-1 flex-col">
      {/* Hero Section */}
      <section className="relative px-6 py-16 md:py-24">
        <CornerDecoration position="top-left" />
        <CornerDecoration position="bottom-right" />

        <div className="max-w-3xl mx-auto text-center">
          <h1 className="font-display text-ink mb-6">
            Learn any skill with guidance from someone who&apos;s been there
          </h1>

          <p className="text-lg text-ink-muted max-w-xl mx-auto mb-10 leading-relaxed">
            SkillSwap connects you with mentors who teach what they know best.
            Browse by topic, find your guide, and start learning.
          </p>

          {/* Illustration */}
          <div className="mb-10">
            <HeroIllustration />
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {authLoading ? (
              <div className="h-12 w-40 bg-cream-dark rounded-lg animate-pulse" />
            ) : isAuthenticated ? (
              <Link href="/dashboard" className="btn btn-primary">
                Continue to Dashboard
              </Link>
            ) : (
              <>
                <Link href="/auth/signup" className="btn btn-primary">
                  Get Started
                </Link>
                <Link href="/auth/signin" className="btn btn-secondary">
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Topics Section */}
      <section className="px-6 py-16 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-4 mb-8">
            <h2 className="font-display text-ink">Browse by Topic</h2>
            <div className="flex-1 h-px bg-cream-dark" />
          </div>

          {topicsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-28 rounded-lg bg-cream animate-pulse"
                />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12 px-6 bg-error-light rounded-lg">
              <p className="text-error font-medium">
                Unable to load topics right now
              </p>
              <p className="text-ink-muted text-sm mt-1">
                Please try again later
              </p>
            </div>
          ) : topicsData && topicsData.items.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {topicsData.items.map((topic, index) => {
                const colorScheme = topicColors[index % topicColors.length];
                return (
                  <Link
                    key={topic.id}
                    href={`/topics/${topic.id}`}
                    className={`group p-5 rounded-lg border-2 ${colorScheme.border} ${colorScheme.bg} transition-all duration-200 hover:translate-y-[-2px] hover:shadow-md`}
                  >
                    <h3 className={`font-display font-semibold ${colorScheme.text} mb-2`}>
                      {topic.name}
                    </h3>
                    {topic.description && (
                      <p className="text-ink-muted text-sm line-clamp-2 leading-relaxed">
                        {topic.description}
                      </p>
                    )}
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 px-6 bg-cream rounded-lg">
              <p className="text-ink-muted">
                No topics available yet. Check back soon.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-4 mb-12">
            <h2 className="font-display text-ink">How It Works</h2>
            <div className="flex-1 h-px bg-cream-dark" />
          </div>

          <div className="grid md:grid-cols-3 gap-8 md:gap-12">
            {/* Step 1 */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-terracotta-light flex items-center justify-center">
                <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                  <circle cx="16" cy="16" r="10" stroke="var(--terracotta)" strokeWidth="2" />
                  <circle cx="16" cy="16" r="4" fill="var(--terracotta)" />
                </svg>
              </div>
              <h3 className="font-display text-lg mb-2">Find a Topic</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                Browse skills you want to learn. Each topic has mentors ready to help.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-olive-light flex items-center justify-center">
                <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                  <circle cx="12" cy="14" r="6" stroke="var(--olive)" strokeWidth="2" />
                  <circle cx="20" cy="14" r="6" stroke="var(--olive)" strokeWidth="2" />
                  <path d="M16 20 L16 26" stroke="var(--olive)" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <h3 className="font-display text-lg mb-2">Connect with a Mentor</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                Read profiles, see reviews, and request mentorship from someone who fits.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-golden-light flex items-center justify-center">
                <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" aria-hidden="true">
                  <path d="M8 24 L16 8 L24 24" stroke="var(--golden)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <circle cx="16" cy="18" r="3" fill="var(--golden)" />
                </svg>
              </div>
              <h3 className="font-display text-lg mb-2">Start Learning</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                Schedule meetings, exchange messages, and grow your skills with guidance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-cream-dark">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-ink-muted">
          <p>SkillSwap — Learn from those who know</p>
          <p>A capstone project</p>
        </div>
      </footer>
    </main>
  );
}
