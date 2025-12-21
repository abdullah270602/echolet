import { SignedIn, SignedOut } from "@clerk/clerk-react";
import { LandingPage, AppPage } from "./pages";

export default function App() {
  return (
    <>
      <SignedOut>
        <LandingPage />
      </SignedOut>
      <SignedIn>
        <AppPage />
      </SignedIn>
    </>
  );
}
