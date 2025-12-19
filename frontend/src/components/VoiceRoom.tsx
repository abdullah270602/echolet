import { useState, useCallback, useEffect, useRef } from "react";
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
}

export function VoiceRoom() {
  const [connectionDetails, setConnectionDetails] =
    useState<TokenResponse | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/livekit/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        throw new Error("Failed to get connection token");
      }

      const data: TokenResponse = await response.json();
      setConnectionDetails(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    setConnectionDetails(null);
  }, []);

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
        {error && <p className="voice-room__error">{error}</p>}
        <button
          className="voice-room__connect-btn"
          onClick={connect}
          disabled={isConnecting}
        >
          {isConnecting ? "Connecting..." : "Start Conversation"}
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
      >
        <RoomContent />
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

function RoomContent() {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const transcriptions = useTranscriptions();

  return (
    <div className="room-content">
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
