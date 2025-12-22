import { useState, useCallback, useEffect, useRef } from "react";
import { useAuth } from "@clerk/clerk-react";
import { motion } from "framer-motion";
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
  identity: string;
  livekit_url: string;
  remaining_seconds: number;
}

export function VoiceRoom() {
  const { getToken } = useAuth();
  const [connectionDetails, setConnectionDetails] =
    useState<TokenResponse | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLimitReached, setIsLimitReached] = useState(false);
  const sessionStartRef = useRef<number | null>(null);

  const reportUsage = useCallback(
    async (talkSeconds: number) => {
      try {
        const authToken = await getToken();
        if (!authToken) return;

        await fetch(`${API_BASE_URL}/livekit/usage`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ talk_seconds: talkSeconds }),
        });
      } catch (err) {
        console.error("Failed to report usage:", err);
      }
    },
    [getToken]
  );

  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);
    setIsLimitReached(false);

    try {
      const authToken = await getToken();

      if (!authToken) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(`${API_BASE_URL}/livekit/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication failed");
        }
        if (response.status === 403) {
          setIsLimitReached(true);
          throw new Error("Daily talk limit reached. Please try again tomorrow.");
        }
        throw new Error("Failed to get connection token");
      }

      const data: TokenResponse = await response.json();
      setConnectionDetails(data);
      sessionStartRef.current = Date.now();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setIsConnecting(false);
    }
  }, [getToken]);

  const disconnect = useCallback(() => {
    // Report usage when disconnecting
    if (sessionStartRef.current) {
      const sessionDuration = Math.floor(
        (Date.now() - sessionStartRef.current) / 1000
      );
      reportUsage(sessionDuration);
      sessionStartRef.current = null;
    }
    setConnectionDetails(null);
  }, [reportUsage]);

  if (!connectionDetails) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg glass rounded-2xl border border-white/10 p-8 relative overflow-hidden"
      >
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 flex flex-col items-center text-center">
          {/* Icon */}
          <motion.div
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-500/20 to-purple-500/20 flex items-center justify-center mb-6 border border-white/10"
          >
            <Mic className="w-10 h-10 text-teal-400" />
          </motion.div>

          {/* Title */}
          <h2 className="text-2xl font-semibold text-white mb-2">
            Voice Assistant Ready
          </h2>
          <p className="text-white/50 mb-8 max-w-sm">
            Speak naturally to test your configuration. The assistant will respond in real-time.
          </p>

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mb-6 px-4 py-3 rounded-lg text-sm w-full ${
                isLimitReached
                  ? "bg-amber-500/10 border border-amber-500/20 text-amber-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}
            >
              {error}
            </motion.div>
          )}

          {/* Connect Button */}
          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            animate={
              !isConnecting && !isLimitReached
                ? { boxShadow: ["0 0 20px rgba(94, 234, 212, 0.3)", "0 0 30px rgba(94, 234, 212, 0.5)", "0 0 20px rgba(94, 234, 212, 0.3)"] }
                : {}
            }
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            onClick={connect}
            disabled={isConnecting || isLimitReached}
            className={`
              w-full py-4 px-8 rounded-xl font-semibold text-white transition-all
              ${isLimitReached
                ? "bg-white/10 cursor-not-allowed text-white/40"
                : "bg-gradient-to-r from-teal-500 to-purple-500"
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
          </motion.button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full max-w-2xl glass rounded-2xl border border-white/10 overflow-hidden"
    >
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
    </motion.div>
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
      <div className="flex items-center justify-center gap-3 py-2">
        <motion.span
          animate={isWarning ? { scale: [1, 1.05, 1] } : {}}
          transition={{ duration: 0.5, repeat: isWarning ? Infinity : 0 }}
          className={`text-3xl font-bold tabular-nums ${
            isWarning ? "text-red-400" : "text-white"
          }`}
        >
          {formatTime(timeLeft)}
        </motion.span>
        <span className="text-sm text-white/40 uppercase tracking-wide">
          Remaining
        </span>
      </div>

      {/* Visualizer */}
      <div className="flex flex-col items-center gap-3 py-4">
        <div
          className={`
            w-48 h-24 rounded-xl flex items-center justify-center
            bg-white/5 border transition-colors duration-300
            ${state === "listening" ? "border-electric-blue/30" : ""}
            ${state === "thinking" ? "border-amber-500/30" : ""}
            ${state === "speaking" ? "border-green-500/30" : ""}
            ${state === "idle" || state === "connecting" ? "border-white/10" : ""}
          `}
        >
          <BarVisualizer
            state={state}
            trackRef={audioTrack}
            barCount={5}
            options={{ minHeight: 8 }}
          />
        </div>

        {/* Status Badge */}
        <div
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
            bg-white/5 border border-white/10
          `}
        >
          <span
            className={`
              w-2 h-2 rounded-full
              ${state === "listening" ? "bg-electric-blue" : ""}
              ${state === "thinking" ? "bg-amber-500 animate-pulse" : ""}
              ${state === "speaking" ? "bg-green-500" : ""}
              ${state === "idle" ? "bg-white/30" : ""}
              ${state === "connecting" ? "bg-white/30 animate-pulse" : ""}
            `}
          />
          <span className="text-white/70">{getStateLabel(state)}</span>
        </div>
      </div>

      {/* Transcript */}
      <TranscriptView
        transcriptions={transcriptions}
        agentTranscriptions={agentTranscriptions}
      />

      {/* Controls */}
      <div className="flex items-center justify-center pt-2 border-t border-white/10">
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
      className="h-48 overflow-y-auto rounded-xl bg-black/20 p-4 scrollbar-thin"
    >
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center">
          <p className="text-white/30 text-sm">Start speaking to begin the conversation</p>
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-start gap-3 ${
                message.isAgent ? "" : "flex-row-reverse"
              }`}
            >
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
                  ${message.isAgent ? "bg-electric-blue text-white" : "bg-green-500 text-white"}
                `}
              >
                {message.isAgent ? "A" : "U"}
              </div>
              <div
                className={`
                  flex-1 max-w-[80%] rounded-xl px-3 py-2
                  ${message.isAgent ? "bg-electric-blue/10" : "bg-green-500/10"}
                `}
              >
                <span className="text-xs text-white/50 block mb-1">
                  {message.isAgent ? "Assistant" : "You"}
                </span>
                <p className="text-sm text-white/90">{message.text}</p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
