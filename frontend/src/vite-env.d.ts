/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CLERK_PUBLISHABLE_KEY: string;
  readonly VITE_API_BASE_URL?: string;
  /** "false" hides the live call and shows only the scripted example. */
  readonly VITE_LIVE_DEMO?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
