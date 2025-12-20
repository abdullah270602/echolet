import { useState, useCallback, useEffect, useRef } from "react";
import { useAuth } from "@clerk/clerk-react";
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

  // Format remaining time for display
  const formatRemainingTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!connectionDetails) {
    return (
      <div className="voice-room">
        <div className="voice-room__hero">
          <div className="voice-room__icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" x2="12" y1="19" y2="22" />
            </svg>
          </div>
          <h2>Voice Assistant</h2>
          <p className="voice-room__description">
            Speak naturally and the assistant will respond.
          </p>
        </div>
        {error && (
          <p className={`voice-room__error ${isLimitReached ? "voice-room__error--limit" : ""}`}>
            {error}
          </p>
        )}
        <button
          className="voice-room__connect-btn"
          onClick={connect}
          disabled={isConnecting || isLimitReached}
        >
          {isConnecting ? "Connecting..." : isLimitReached ? "Limit Reached" : "Start Conversation"}
        </button>
      </div>
    );
  }

  return (
    <div className="voice-room">
      <LiveKitRoom
        token={connectionDetails.token}
        serverUrl={connectionDetails.livekit_url}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={disconnect}
        options={{
          publishDefaults: {
            audioPreset: { maxBitrate: 32000 },
          },
        }}
        connectOptions={{
          participantMetadata: JSON.stringify({
            remaining_seconds: connectionDetails.remaining_seconds,
          }),
        }}
      >
        <RoomContent remainingSeconds={connectionDetails.remaining_seconds} />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

function RoomContent({ remainingSeconds }: { remainingSeconds: number }) {
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

  return (
    <div className="room-content">
      <div className="time-remaining">
        <span className={`time-remaining__value ${timeLeft <= 30 ? "time-remaining__value--warning" : ""}`}>
          {formatTime(timeLeft)}
        </span>
        <span className="time-remaining__label">remaining</span>
      </div>

      <div className="visualizer-section">
        <div className={`visualizer-container visualizer--${state}`}>
          <BarVisualizer
            state={state}
            trackRef={audioTrack}
            barCount={5}
            options={{ minHeight: 8 }}
          />
        </div>
        <div className={`status-badge status-badge--${state}`}>
          <span className="status-badge__dot" />
          <span className="status-badge__text">{getStateLabel(state)}</span>
        </div>
      </div>

      <TranscriptView
        transcriptions={transcriptions}
        agentTranscriptions={agentTranscriptions}
      />

      <div className="control-section">
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
    <div className="transcript" ref={scrollRef}>
      {messages.length === 0 ? (
        <div className="transcript__empty">
          <p>Start speaking to begin the conversation</p>
        </div>
      ) : (
        <div className="transcript__messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.isAgent ? "message--agent" : "message--user"}`}
            >
              <div className="message__avatar">
                {message.isAgent ? "A" : "U"}
              </div>
              <div className="message__content">
                <span className="message__sender">
                  {message.isAgent ? "Assistant" : "You"}
                </span>
                <p className="message__text">{message.text}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
