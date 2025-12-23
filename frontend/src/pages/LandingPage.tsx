import {
  Navbar,
  HeroSection,
  ComparisonSection,
  SolutionSection,
  FeatureSpotlight,
  WaitlistSection,
} from '../components/landing';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-midnight-900">
      <Navbar />

      <main>
        <HeroSection />
        <ComparisonSection />
        <SolutionSection />
        <FeatureSpotlight />
        <WaitlistSection />
      </main>
    </div>
  );
}
