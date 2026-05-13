import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import "./index.css";
import App from "./App.tsx";
import { LandingPage } from "./pages";
import { ClerkProvider } from "@clerk/clerk-react";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

// Without a Clerk key (e.g. the landing-only Vercel deploy) there is no sign-in or
// dashboard, so serve just the landing page instead of failing to boot.
const app = PUBLISHABLE_KEY ? (
  <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
    <App />
  </ClerkProvider>
) : (
  <LandingPage />
);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      {app}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#ffffff",
            color: "var(--color-ink)",
            border: "2px solid var(--color-ink)",
            borderRadius: 0,
          },
          success: { iconTheme: { primary: "var(--color-accent)", secondary: "#ffffff" } },
          error: { iconTheme: { primary: "#b91c1c", secondary: "#ffffff" } },
        }}
      />
    </BrowserRouter>
  </StrictMode>
);
