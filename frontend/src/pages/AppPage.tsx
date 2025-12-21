import { UserButton } from "@clerk/clerk-react";
import { VoiceRoom } from "../components/VoiceRoom";

export function AppPage() {
  return (
    <div className="app-container">
      <header className="w-full flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Echolet</h1>
        <UserButton />
      </header>

      <main className="w-full">
        <VoiceRoom />
      </main>
    </div>
  );
}
