import { useState, useCallback, useEffect, useRef } from "react";
import { useAuth } from "@clerk/clerk-react";
import { Mic, Loader2 } from "lucide-react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
  useTranscriptions,
} from "@livekit/components-react";
import "@livekit/components-styles";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

interface TokenResponse {
  token: string;
  room_name: string;
  session_id: number;
  identity: string;
  livekit_url: string;
  remaining_seconds: number;
}

interface VoiceRoomProps {
  agentId: number;
}

export function VoiceRoom({ agentId }: VoiceRoomProps) {
  const { getToken } = useAuth();
  const [connectionDetails, setConnectionDetails] =
    useState<TokenResponse | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLimitReached, setIsLimitReached] = useState(false);

  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);
    setIsLimitReached(false);

    try {
      const authToken = await getToken();

      if (!authToken) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_BASE_URL}/session/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ agent_id: agentId }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication failed");
        }
        if (response.status === 403) {
          setIsLimitReached(true);
          throw new Error("Daily talk limit reached. Please try again tomorrow.");
        }
        if (response.status === 404) {
          throw new Error("Agent not found");
        }
        throw new Error("Failed to start session");
      }

      const data: TokenResponse = await response.json();
      setConnectionDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setIsConnecting(false);
    }
  }, [getToken, agentId]);

  // Talk time is recorded server-side by the voice agent when the call ends.
  const disconnect = useCallback(() => {
    setConnectionDetails(null);
  }, []);

  if (!connectionDetails) {
    return (
      <div className="w-full max-w-lg border-2 border-ink bg-white p-8 relative">
        <div className="flex flex-col items-center text-center">
          {/* Icon */}
          <div className="w-16 h-16 bg-paper flex items-center justify-center mb-6 border border-rule">
            <Mic className="w-8 h-8 text-accent" />
          </div>

          {/* Title */}
          <h2 className="font-display text-2xl font-bold text-ink mb-2">
            Voice Assistant Ready
          </h2>
          <p className="text-muted mb-8 max-w-sm">
            Speak naturally to test your configuration. The assistant will respond in real-time.
          </p>

          {/* Error */}
          {error && (
            <div
              role="alert"
              className={`mb-6 px-4 py-3 text-sm w-full border ${
                isLimitReached
                  ? "bg-amber-50 border-amber-300 text-amber-800"
                  : "bg-red-50 border-red-300 text-red-700"
              }`}
            >
              {error}
            </div>
          )}

          {/* Connect Button */}
          <button
            onClick={connect}
            disabled={isConnecting || isLimitReached}
            className={`
              w-full min-h-11 py-3 px-6 font-semibold text-white transition-colors
              ${isLimitReached
                ? "bg-rule cursor-not-allowed text-muted"
                : "bg-accent hover:bg-accent-dark"
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            <span className="flex items-center justify-center gap-2">
              {isConnecting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Connecting...
                </>
              ) : isLimitReached ? (
                "Limit Reached"
              ) : (
                "Start Conversation"
              )}
            </span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl border-2 border-ink bg-white overflow-hidden">
      <LiveKitRoom
        token={connectionDetails.token}
        serverUrl={connectionDetails.livekit_url}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={disconnect}
      >
        <RoomContent remainingSeconds={connectionDetails.remaining_seconds} />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

function RoomContent({
  remainingSeconds,
}: {
  remainingSeconds: number;
}) {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const transcriptions = useTranscriptions();
  const [timeLeft, setTimeLeft] = useState(remainingSeconds);

  // Countdown timer
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const isWarning = timeLeft <= 30;

  return (
    <div className="p-6 flex flex-col gap-4">
      {/* Timer */}
      <div className="flex items-center justify-between gap-4 border-b border-rule pb-4">
        <div className="flex items-center gap-2">
          <span
            className={`
              w-2.5 h-2.5 rounded-full
              ${state === "listening" ? "bg-accent" : ""}
              ${state === "thinking" ? "bg-amber-600 animate-pulse" : ""}
              ${state === "speaking" ? "bg-accent" : ""}
              ${state === "idle" || state === "connecting" ? "bg-muted" : ""}
            `}
          />
          <span className="font-medium text-ink">{getStateLabel(state)}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`font-display text-xl font-bold tabular-nums ${
              isWarning ? "text-red-700" : "text-ink"
            }`}
          >
            {formatTime(timeLeft)}
          </span>
          <span className="text-xs text-muted uppercase tracking-wide">
            Remaining
          </span>
        </div>
      </div>

      {/* Visualizer */}
      <div className="demo-bars my-4 flex h-24 items-center justify-center bg-paper/50 border border-rule">
        <BarVisualizer
          state={state}
          trackRef={audioTrack}
          barCount={7}
          options={{ minHeight: 8 }}
        />
      </div>

      {/* Transcript */}
      <TranscriptView
        transcriptions={transcriptions}
        agentTranscriptions={agentTranscriptions}
      />

      {/* Controls */}
      <div className="flex items-center justify-center pt-4 border-t border-rule">
        <VoiceAssistantControlBar />
      </div>
    </div>
  );
}

function getStateLabel(state: string): string {
  switch (state) {
    case "listening":
      return "Listening";
    case "thinking":
      return "Thinking";
    case "speaking":
      return "Speaking";
    case "idle":
      return "Ready";
    case "connecting":
      return "Connecting";
    default:
      return state;
  }
}

interface TranscriptMessage {
  id: string;
  text: string;
  isAgent: boolean;
  timestamp: number;
}

function TranscriptView({
  transcriptions,
  agentTranscriptions,
}: {
  transcriptions: ReturnType<typeof useTranscriptions>;
  agentTranscriptions: ReturnType<typeof useVoiceAssistant>["agentTranscriptions"];
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);

  useEffect(() => {
    const newMessages: TranscriptMessage[] = [];

    if (agentTranscriptions) {
      agentTranscriptions.forEach((t, index) => {
        if (t.text && t.text.trim()) {
          newMessages.push({
            id: `agent-${index}-${t.text.substring(0, 10)}`,
            text: t.text,
            isAgent: true,
            timestamp: Date.now() - (agentTranscriptions.length - index) * 1000,
          });
        }
      });
    }

    if (transcriptions) {
      transcriptions.forEach((t, index) => {
        if (t.text && t.text.trim()) {
          const isFromAgent = agentTranscriptions?.some(
            (at) => at.text === t.text
          );
          if (!isFromAgent) {
            newMessages.push({
              id: `user-${index}-${t.text.substring(0, 10)}`,
              text: t.text,
              isAgent: false,
              timestamp: Date.now() - (transcriptions.length - index) * 1000,
            });
          }
        }
      });
    }

    newMessages.sort((a, b) => a.timestamp - b.timestamp);
    setMessages(newMessages);
  }, [transcriptions, agentTranscriptions]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={scrollRef}
      className="h-48 overflow-y-auto bg-paper/50 border border-rule p-4"
    >
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center">
          <p className="text-muted text-sm">Start speaking to begin the conversation</p>
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-3 ${
                message.isAgent ? "" : "flex-row-reverse"
              }`}
            >
              <div
                className={`
                  w-7 h-7 flex items-center justify-center text-xs font-semibold border
                  ${message.isAgent ? "bg-accent border-accent text-white" : "bg-white border-ink text-ink"}
                `}
              >
                {message.isAgent ? "A" : "U"}
              </div>
              <div
                className={`
                  flex-1 max-w-[80%] px-3 py-2 border
                  ${message.isAgent ? "bg-white border-ink" : "bg-paper border-rule"}
                `}
              >
                <span className="text-xs font-semibold text-muted block mb-1">
                  {message.isAgent ? "Assistant" : "You"}
                </span>
                <p className="text-sm text-ink">{message.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
