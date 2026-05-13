import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import "./index.css";
import App from "./App.tsx";
import { ClerkProvider } from "@clerk/clerk-react";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Clerk Publishable Key");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
        <App />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#ffffff',
              color: 'var(--color-ink)',
              border: '2px solid var(--color-ink)',
              borderRadius: 0,
            },
            success: { iconTheme: { primary: 'var(--color-accent)', secondary: '#ffffff' } },
            error: { iconTheme: { primary: '#b91c1c', secondary: '#ffffff' } },
          }}
        />
      </ClerkProvider>
    </BrowserRouter>
  </StrictMode>
);
