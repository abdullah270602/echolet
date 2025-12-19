import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/clerk-react";
import { VoiceRoom } from "./components/VoiceRoom";

export default function App() {
  return (
    <div className="container">
      <header>
        <h1>Echolet</h1>
        <SignedOut>
          <div className="auth-buttons">
            <SignInButton />
            <SignUpButton />
          </div>
        </SignedOut>
        <SignedIn>
          <UserButton />
        </SignedIn>
      </header>

      <main>
        <SignedIn>
          <VoiceRoom />
        </SignedIn>
        <SignedOut>
          <p>Sign in to start a voice conversation with the AI assistant.</p>
        </SignedOut>
      </main>
    </div>
  );
}
