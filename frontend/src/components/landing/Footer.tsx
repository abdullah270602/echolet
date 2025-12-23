import { AudioWaveform } from 'lucide-react';

export function Footer() {
  return (
    <footer className="py-12 border-t border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo & Copyright */}
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="flex items-center gap-2">
              <AudioWaveform className="w-6 h-6 text-teal-400" />
              <span className="text-lg font-semibold text-white">Echolet</span>
            </div>
            <p className="text-sm text-white/40">
              © {new Date().getFullYear()} Echolet. All rights reserved.
            </p>
          </div>

          {/* Contact */}
          <div className="flex flex-col items-center md:items-end gap-1">
            <p className="text-sm text-white/60">Contact us</p>
            <div className="flex flex-wrap justify-center gap-4">
              <a
                href="mailto:abdullah@echolet.xyz"
                className="text-sm text-teal-400 hover:text-teal-300 transition-colors"
              >
                abdullah@echolet.xyz
              </a>
              <a
                href="mailto:arslan@echolet.xyz"
                className="text-sm text-teal-400 hover:text-teal-300 transition-colors"
              >
                arslan@echolet.xyz
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
