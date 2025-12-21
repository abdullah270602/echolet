import { useState } from 'react';
import {
  Navbar,
  HeroSection,
  ProblemSection,
  SolutionSection,
  FeatureSpotlight,
  CTAFooter,
} from '../components/landing';
import { AudioModal } from '../components/ui';

export function LandingPage() {
  const [isAudioModalOpen, setIsAudioModalOpen] = useState(false);

  const handleDemoClick = () => {
    setIsAudioModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-midnight-900">
      <Navbar onDemoClick={handleDemoClick} />

      <main>
        <HeroSection onDemoClick={handleDemoClick} />
        <ProblemSection />
        <SolutionSection />
        <FeatureSpotlight />
        <CTAFooter />
      </main>

      <AudioModal
        isOpen={isAudioModalOpen}
        onClose={() => setIsAudioModalOpen(false)}
      />
    </div>
  );
}
