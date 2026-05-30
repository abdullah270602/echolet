import { useCallback, useEffect, useRef, useState } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  BarVisualizer,
  useConnectionState,
  useIsSpeaking,
  useLocalParticipant,
  useTranscriptions,
  useVoiceAssistant,
  useRoomContext,
} from '@livekit/components-react';
import '@livekit/components-styles';
import { ConnectionState } from 'livekit-client';
import { Mic, MicOff, PhoneOff } from 'lucide-react';
import type { DemoSession } from '../../services/demoApi';
import { Typing } from './Typing';
import { parseTicket, type CallResult, type Ticket } from './ticket';

const AGENT = 'Emma';
const PICKUP_TIMEOUT_SECONDS = 15; // give up if the agent has not joined by then
const TICKET_AT_SECONDS = 10; // start the write-up this long before the cap
const FINAL_ATTR = 'lk.transcription_final';

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;

const pill =
  'inline-flex min-h-11 items-center gap-2 rounded-full border-2 px-5 font-semibold transition-colors';

type Mode = 'pickup' | 'emma' | 'you' | 'thinking' | 'listening' | 'muted';

function Room({
  maxSeconds,
  micLost,
  onEnd,
  onError,
}: {
  maxSeconds: number;
  micLost: boolean;
  onEnd: (r: CallResult) => void;
  onError: (message: string) => void;
}) {
  const { state, audioTrack, agent } = useVoiceAssistant();
  const { localParticipant, isMicrophoneEnabled } = useLocalParticipant();
  const connection = useConnectionState();
  const youSpeaking = useIsSpeaking(localParticipant);
  const lines = useTranscriptions().filter((t) => t.text.trim());

  const [elapsed, setElapsed] = useState(0);
  const [writing, setWriting] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);
  const meterRef = useRef<HTMLSpanElement>(null);
  const finishing = useRef(false);
  const wasConnected = useRef(false);
  const pickedUp = useRef(false);
  // A ticket the agent pushed because it ended the call itself (caller said goodbye).
  const pushed = useRef<Ticket | null>(null);
  const room = useRoomContext();

  useEffect(() => {
    room.registerRpcMethod('echolet.ticket.push', async (data) => {
      pushed.current = parseTicket(data.payload);
      return 'ok';
    });
    return () => room.unregisterRpcMethod('echolet.ticket.push');
  }, [room]);

  const left = maxSeconds - elapsed;
  const muted = !isMicrophoneEnabled;
  const spoke = lines.some((t) => t.participantInfo.identity === localParticipant.identity);
  const spokeRef = useRef(spoke);
  spokeRef.current = spoke;
  if (['listening', 'thinking', 'speaking', 'idle'].includes(state)) pickedUp.current = true;

  // Ask the agent for the ticket, then hand the call result up. Skips the request if
  // the visitor never spoke: there is nothing to write about.
  const finish = useCallback(async () => {
    if (finishing.current) return;
    finishing.current = true;
    setWriting(true);
    localParticipant.setMicrophoneEnabled(false).catch(() => {});
    let ticket = pushed.current;
    if (!ticket && spokeRef.current && agent) {
      try {
        const raw = await localParticipant.performRpc({
          destinationIdentity: agent.identity,
          method: 'echolet.ticket',
          payload: '',
          responseTimeout: 15000,
        });
        ticket = parseTicket(raw);
      } catch {
        // falls through to "couldn't be written"
      }
    }
    onEnd({ ticket, spoke: spokeRef.current });
  }, [agent, localParticipant, onEnd]);

  useEffect(() => {
    const id = setInterval(() => setElapsed((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (left <= TICKET_AT_SECONDS) void finish();
  }, [left, finish]);

  useEffect(() => {
    if (state === 'failed' || (!pickedUp.current && elapsed >= PICKUP_TIMEOUT_SECONDS)) {
      onError(`${AGENT} didn't pick up. The front desk may be busy, so try again in a moment.`);
    }
  }, [state, elapsed, onError]);

  // The room closed under us (agent hung up, network lost).
  useEffect(() => {
    if (connection === ConnectionState.Connected) wasConnected.current = true;
    else if (connection === ConnectionState.Disconnected && wasConnected.current && !finishing.current) {
      finishing.current = true;
      if (pickedUp.current) onEnd({ ticket: pushed.current, spoke: spokeRef.current });
      else onError('The connection dropped. Try the call again.');
    }
  }, [connection, onEnd, onError]);

  // Mic level meter, written straight to the DOM so it doesn't re-render the room.
  useEffect(() => {
    const id = setInterval(() => {
      const level = localParticipant.isMicrophoneEnabled ? Math.min(1, localParticipant.audioLevel * 3) : 0;
      if (meterRef.current) meterRef.current.style.transform = `scaleX(${level})`;
    }, 80);
    return () => clearInterval(id);
  }, [localParticipant]);

  const lastText = lines[lines.length - 1]?.text;
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [lines.length, lastText]);

  let mode: Mode = 'listening';
  if (!pickedUp.current) mode = 'pickup';
  else if (state === 'speaking') mode = 'emma';
  else if (youSpeaking && !muted) mode = 'you';
  else if (state === 'thinking') mode = 'thinking';
  else if (muted) mode = 'muted';

  if (writing) {
    return (
      <div role="status" className="flex min-h-[22rem] flex-col justify-center">
        <p className="font-display font-wide text-2xl font-extrabold tracking-[-0.02em]">
          {AGENT} is writing up your call
        </p>
        <p className="mt-2 text-muted">Her notes will be ready in a moment.</p>
        <Typing className="mt-6" />
      </div>
    );
  }

  const label: Record<Mode, string> = {
    pickup: elapsed < 3 ? 'Calling Brightside Dental' : `${AGENT} is picking up`,
    emma: `${AGENT} is speaking`,
    you: 'You are speaking',
    thinking: `${AGENT} is thinking`,
    listening: 'Listening',
    muted: 'Your mic is muted',
  };

  return (
    <div className="flex min-h-[22rem] flex-col">
      <div className="flex items-center justify-between gap-4">
        <p className="flex items-center gap-3 font-semibold">
          <span className={mode === 'emma' || mode === 'pickup' ? 'text-slip' : ''}>{label[mode]}</span>
          {(mode === 'thinking' || mode === 'pickup') && <Typing />}
        </p>
        <p
          className={`text-sm tabular-nums transition-colors ${left <= 15 ? 'font-bold text-[#ff8a80]' : 'text-muted'}`}
        >
          <span className="sr-only">Time left </span>
          {fmt(Math.max(0, left))}
        </p>
      </div>

      <div className="demo-bars my-5 flex h-16 items-center justify-center" aria-hidden="true">
        <BarVisualizer state={state} trackRef={audioTrack} barCount={7} options={{ minHeight: 6 }} />
      </div>

      {micLost && (
        <p role="alert" className="mb-3 rounded-lg bg-[#131a4f]/50 px-3 py-2 text-sm">
          Your microphone stopped working. Check it is connected and allowed, then end the call and try again.
        </p>
      )}

      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-label="Live captions"
        tabIndex={0}
        className="thin-scroll transcript-fade h-40 space-y-3 overflow-y-auto pt-6 text-[15px] leading-relaxed"
      >
        {lines.length === 0 && (
          <p className="text-muted">
            {pickedUp.current ? 'Say hello. Captions appear here as you talk.' : 'Captions appear here once the call starts.'}
          </p>
        )}
        {lines.map((t, i) => {
          const you = t.participantInfo.identity === localParticipant.identity;
          const final = t.streamInfo.attributes?.[FINAL_ATTR] !== 'false';
          return (
            <p key={t.streamInfo.id ?? i} className="line-in">
              <span className={`font-semibold ${you ? 'text-ink' : 'text-slip'}`}>{you ? 'You' : AGENT}: </span>
              <span className={final ? 'text-ink/90' : 'text-ink/55'}>{t.text}</span>
            </p>
          );
        })}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          aria-pressed={muted}
          onClick={() => localParticipant.setMicrophoneEnabled(muted).catch(() => {})}
          className={`${pill} ${muted ? 'border-slip bg-slip text-[#131a4f]' : 'border-rule text-ink hover:border-ink'}`}
        >
          {muted ? <MicOff aria-hidden="true" className="h-4 w-4" /> : <Mic aria-hidden="true" className="h-4 w-4" />}
          {muted ? 'Muted' : 'Mic on'}
          <span aria-hidden="true" className="h-1.5 w-10 overflow-hidden rounded-full bg-[#131a4f]/40">
            <span
              ref={meterRef}
              className="block h-full origin-left rounded-full bg-[#3ddc97] transition-transform duration-75"
              style={{ transform: 'scaleX(0)' }}
            />
          </span>
        </button>
        <button
          type="button"
          onClick={() => void finish()}
          className={`${pill} border-slip text-slip hover:bg-slip hover:text-[#131a4f]`}
        >
          <PhoneOff aria-hidden="true" className="h-4 w-4" />
          End call
        </button>
      </div>
    </div>
  );
}

export default function LiveDemoRoom({
  session,
  onEnd,
  onError,
}: {
  session: DemoSession;
  onEnd: (r: CallResult) => void;
  onError: (message: string) => void;
}) {
  const [micLost, setMicLost] = useState(false);
  const fail = useCallback(() => onError('The connection dropped. Try the call again.'), [onError]);
  return (
    <LiveKitRoom
      token={session.token}
      serverUrl={session.livekit_url}
      connect
      audio
      video={false}
      onError={fail}
      onMediaDeviceFailure={() => setMicLost(true)}
    >
      <Room maxSeconds={session.max_seconds} micLost={micLost} onEnd={onEnd} onError={onError} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}
