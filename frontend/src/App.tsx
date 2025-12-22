import { SignedIn, SignedOut, RedirectToSignIn } from "@clerk/clerk-react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LandingPage, SignInPage } from "./pages";
import { DashboardLayout } from "./components/dashboard";
import {
  AgentSandbox,
  AgentConfiguration,
  CallHistory,
  Settings,
} from "./pages/dashboard";

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/sign-in/*" element={<SignInPage />} />

      {/* Protected dashboard routes */}
      <Route
        path="/app"
        element={
          <>
            <SignedIn>
              <DashboardLayout />
            </SignedIn>
            <SignedOut>
              <RedirectToSignIn />
            </SignedOut>
          </>
        }
      >
        <Route index element={<AgentSandbox />} />
        <Route path="config" element={<AgentConfiguration />} />
        <Route path="history" element={<CallHistory />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
