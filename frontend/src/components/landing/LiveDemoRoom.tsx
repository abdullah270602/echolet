import { useEffect, useRef, useState } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  BarVisualizer,
  useVoiceAssistant,
  useTranscriptions,
  useLocalParticipant,
} from '@livekit/components-react';
import '@livekit/components-styles';
import type { DemoSession } from '../../services/demoApi';

const STATE_LABEL: Record<string, string> = {
  disconnected: 'Connecting',
  connecting: 'Connecting',
  initializing: 'Receptionist is joining',
  listening: 'Listening to you',
  thinking: 'Thinking',
  speaking: 'Speaking',
  idle: 'Ready',
};

// The agent enforces the cap, says goodbye and closes the room. The browser only
// hangs up on its own if that hasn't happened shortly after the cap.
const CLIENT_GRACE_SECONDS = 15;

function fmt(s: number) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function Room({ maxSeconds, onEnd }: { maxSeconds: number; onEnd: () => void }) {
  const { state, audioTrack } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();
  const lines = useTranscriptions().filter((t) => t.text.trim());
  const [left, setLeft] = useState(maxSeconds);
  const logRef = useRef<HTMLDivElement>(null);
  const lastText = lines[lines.length - 1]?.text;

  useEffect(() => {
    const id = setInterval(() => setLeft((n) => n - 1), 1000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => {
    if (left <= -CLIENT_GRACE_SECONDS) onEnd();
  }, [left, onEnd]);
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [lines.length, lastText]);

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="font-medium text-ink" role="status">
          {STATE_LABEL[state] ?? state}
        </p>
        <p className="tabular-nums text-muted">{fmt(Math.max(0, left))} left</p>
      </div>

      <div className="demo-bars my-6 flex h-20 items-center justify-center" aria-hidden="true">
        <BarVisualizer state={state} trackRef={audioTrack} barCount={7} options={{ minHeight: 6 }} />
      </div>

      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-label="Live captions"
        tabIndex={0}
        className="thin-scroll transcript-fade h-48 space-y-3 overflow-y-auto pt-6 text-[15px] leading-relaxed"
      >
        {lines.length === 0 && <p className="text-muted">Say hello. Captions appear here as you talk.</p>}
        {lines.map((t, i) => {
          const you = t.participantInfo.identity === localParticipant.identity;
          return (
            <p key={t.streamInfo.id ?? i}>
              <span className={you ? 'font-semibold text-ink' : 'font-semibold text-slip'}>{you ? 'You' : 'Receptionist'}: </span>
              <span className="text-ink/80">{t.text}</span>
            </p>
          );
        })}
      </div>

      <button
        onClick={onEnd}
        className="mt-6 inline-flex min-h-11 items-center rounded-full border-2 border-[#f4a3b3] px-5 font-semibold text-[#f4a3b3] transition-colors hover:bg-[#f4a3b3] hover:text-[#1b2559]"
      >
        End call
      </button>
    </div>
  );
}

export default function LiveDemoRoom({
  session,
  onEnd,
  onError,
}: {
  session: DemoSession;
  onEnd: () => void;
  onError: () => void;
}) {
  return (
    <LiveKitRoom
      token={session.token}
      serverUrl={session.livekit_url}
      connect
      audio
      video={false}
      onDisconnected={onEnd}
      onError={onError}
    >
      <Room maxSeconds={session.max_seconds} onEnd={onEnd} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}
