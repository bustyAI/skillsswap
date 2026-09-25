"use client";

import Link from "next/link";
import { useAuth } from "@/providers/auth-provider";
import { useTopics } from "@/hooks/use-topics";

function HeroIllustration() {
  return (
    <svg
      viewBox="0 0 480 280"
      fill="none"
      className="w-full max-w-xl mx-auto"
      aria-hidden="true"
    >
      <style>{`
        @media (prefers-reduced-motion: no-preference) {
          .hero-frame { animation: fade-in 0.4s ease-out both; }
          .hero-learner { animation: fade-in 0.5s ease-out 0.2s both; }
          .hero-mentor { animation: fade-in 0.5s ease-out 0.3s both; }
          .hero-skill { animation: fade-in 0.5s ease-out 0.4s both; }
          .hero-line-1 {
            stroke-dasharray: 280;
            stroke-dashoffset: 280;
            animation: draw-path 0.8s ease-out 0.5s forwards;
          }
          .hero-line-2 {
            stroke-dasharray: 280;
            stroke-dashoffset: 280;
            animation: draw-path 0.8s ease-out 0.7s forwards;
          }
          .hero-accent { animation: fade-in 0.3s ease-out 1s both; }
          @keyframes fade-in {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          @keyframes draw-path {
            to { stroke-dashoffset: 0; }
          }
        }
      `}</style>

      {/* Background frame */}
      <rect className="hero-frame" x="40" y="30" width="400" height="220" rx="8" fill="white" stroke="var(--cream-dark)" strokeWidth="3" />

      {/* Connection arcs - animated */}
      <path
        className="hero-line-1"
        d="M140 140 Q240 60 340 140"
        stroke="var(--golden)"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="hero-line-2"
        d="M140 140 Q240 220 340 140"
        stroke="var(--teal)"
        strokeWidth="4"
        fill="none"
      />

      {/* Left figure - the learner */}
      <g className="hero-learner">
        <circle cx="140" cy="140" r="44" fill="var(--terracotta-light)" stroke="var(--terracotta)" strokeWidth="3" />
        <circle cx="140" cy="125" r="14" fill="var(--terracotta)" />
        <path d="M126 145 Q140 165 154 145" stroke="var(--terracotta)" strokeWidth="4" fill="none" strokeLinecap="round" />
        <rect x="110" y="195" width="60" height="24" rx="4" fill="var(--terracotta)" />
        <text x="140" y="212" textAnchor="middle" fill="white" style={{ fontSize: "12px", fontWeight: 700, fontFamily: "var(--font-body)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          You
        </text>
      </g>

      {/* Center - the skill badge */}
      <g className="hero-skill" transform="translate(240, 140)">
        <polygon points="0,-38 33,-19 33,19 0,38 -33,19 -33,-19" fill="var(--golden)" stroke="var(--golden-dark)" strokeWidth="3" />
        <text y="6" textAnchor="middle" fill="white" style={{ fontSize: "14px", fontWeight: 700, fontFamily: "var(--font-display)" }}>
          SKILL
        </text>
      </g>

      {/* Right figure - the mentor */}
      <g className="hero-mentor">
        <circle cx="340" cy="140" r="44" fill="var(--olive-light)" stroke="var(--olive)" strokeWidth="3" />
        <circle cx="340" cy="125" r="14" fill="var(--olive)" />
        <path d="M326 145 Q340 165 354 145" stroke="var(--olive)" strokeWidth="4" fill="none" strokeLinecap="round" />
        <rect x="358" y="108" width="22" height="28" rx="2" fill="var(--olive)" stroke="var(--olive-dark)" strokeWidth="2" />
        <line x1="363" y1="115" x2="375" y2="115" stroke="var(--olive-light)" strokeWidth="2" />
        <line x1="363" y1="121" x2="372" y2="121" stroke="var(--olive-light)" strokeWidth="2" />
        <line x1="363" y1="127" x2="375" y2="127" stroke="var(--olive-light)" strokeWidth="2" />
        <rect x="310" y="195" width="60" height="24" rx="4" fill="var(--olive)" />
        <text x="340" y="212" textAnchor="middle" fill="white" style={{ fontSize: "12px", fontWeight: 700, fontFamily: "var(--font-body)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Mentor
        </text>
      </g>

      {/* Corner accents */}
      <circle className="hero-accent" cx="60" cy="50" r="8" fill="var(--terracotta)" />
      <circle className="hero-accent" cx="420" cy="50" r="8" fill="var(--olive)" />
      <rect className="hero-accent" x="52" y="230" width="16" height="16" fill="var(--teal)" />
      <polygon className="hero-accent" points="420,230 428,246 412,246" fill="var(--golden)" />
    </svg>
  );
}


export default function Home() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: topicsData, isLoading: topicsLoading, error } = useTopics();

  return (
    <main className="flex flex-1 flex-col">
      {/* Hero Section */}
      <section className="relative px-6 py-20 md:py-28 border-b-[3px] border-ink">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-sm font-bold uppercase tracking-widest text-terracotta mb-4">
              Mentorship Made Simple
            </p>
            <h1 className="font-display text-ink mb-6 max-w-3xl mx-auto">
              Learn any skill with guidance from someone who&apos;s been there
            </h1>
            <p className="text-xl text-ink-muted max-w-2xl mx-auto leading-relaxed">
              SkillSwap connects you with mentors who teach what they know best.
              Browse by topic, find your guide, and start learning.
            </p>
          </div>

          <div className="mb-12">
            <HeroIllustration />
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {authLoading ? (
              <div className="h-14 w-48 bg-cream-dark rounded-lg animate-pulse" />
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
      <section className="px-6 py-20 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-6 mb-10">
            <h2 className="font-display text-ink">Browse by Topic</h2>
            <div className="flex-1 h-[3px] bg-ink" />
          </div>

          {topicsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-32 rounded-lg bg-cream-dark animate-pulse" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12 px-6 bg-error-light rounded-lg border-[3px] border-error/20">
              <p className="text-error font-bold">Unable to load topics right now</p>
              <p className="text-ink-muted text-sm mt-1">Please try again later</p>
            </div>
          ) : topicsData && topicsData.items.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {topicsData.items.map((topic, index) => {
                const colors = [
                  "bg-terracotta-light border-terracotta text-terracotta-dark hover:bg-terracotta hover:text-white",
                  "bg-golden-light border-golden text-golden-dark hover:bg-golden hover:text-white",
                  "bg-teal-light border-teal text-teal-dark hover:bg-teal hover:text-white",
                  "bg-olive-light border-olive text-olive-dark hover:bg-olive hover:text-white",
                ];
                const colorClass = colors[index % colors.length];
                const staggerClass = `stagger-${Math.min(index + 1, 6)}`;
                return (
                  <Link
                    key={topic.id}
                    href={`/topics/${topic.id}`}
                    className={`group block p-6 rounded-lg border-[3px] ${colorClass} animate-fade-up ${staggerClass} transition-all duration-150 hover:translate-y-[-3px] hover:shadow-lg`}
                  >
                    <h3 className="font-display font-bold text-lg mb-2">
                      {topic.name}
                    </h3>
                    {topic.description && (
                      <p className="text-sm line-clamp-2 leading-relaxed opacity-80 group-hover:opacity-100">
                        {topic.description}
                      </p>
                    )}
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 px-6 bg-cream rounded-lg border-[3px] border-cream-dark">
              <p className="text-ink-muted font-medium">No topics available yet. Check back soon.</p>
            </div>
          )}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-20 border-b-[3px] border-ink">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-6 mb-14">
            <h2 className="font-display text-ink">How It Works</h2>
            <div className="flex-1 h-[3px] bg-ink" />
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            {/* Step 1 */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-terracotta flex items-center justify-center border-[3px] border-terracotta-dark">
                <span className="font-display font-bold text-2xl text-white">1</span>
              </div>
              <h3 className="font-display text-xl font-bold mb-3">Find a Topic</h3>
              <p className="text-ink-muted leading-relaxed">
                Browse skills you want to learn. Each topic has mentors ready to help.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-golden flex items-center justify-center border-[3px] border-golden-dark">
                <span className="font-display font-bold text-2xl text-white">2</span>
              </div>
              <h3 className="font-display text-xl font-bold mb-3">Connect</h3>
              <p className="text-ink-muted leading-relaxed">
                Read profiles, see reviews, and request mentorship from someone who fits.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-5 rounded-full bg-teal flex items-center justify-center border-[3px] border-teal-dark">
                <span className="font-display font-bold text-2xl text-white">3</span>
              </div>
              <h3 className="font-display text-xl font-bold mb-3">Start Learning</h3>
              <p className="text-ink-muted leading-relaxed">
                Schedule meetings, exchange messages, and grow your skills with guidance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-10 bg-ink text-cream">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="font-display font-bold text-lg">SkillSwap</p>
          <p className="text-sm text-cream/70">Learn from those who know</p>
        </div>
      </footer>
    </main>
  );
}
