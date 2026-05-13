import { SignIn } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { dark } from "@clerk/themes";

export function SignInPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="min-h-screen bg-midnight-900 relative overflow-hidden flex items-center justify-center"
    >
      {/* Ambient glow orbs - static/slow moving */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Top-right teal glow */}
        <motion.div
          animate={{
            x: [0, 20, 0],
            y: [0, -10, 0],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute -top-32 -right-32 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl"
        />
        {/* Bottom-left purple glow */}
        <motion.div
          animate={{
            x: [0, -20, 0],
            y: [0, 10, 0],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className="absolute -bottom-32 -left-32 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
        />
        {/* Center subtle glow behind the sign-in box */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-br from-teal-500/10 to-purple-500/10 rounded-full blur-3xl" />
      </div>

      {/* Back to Home link - top left */}
      <Link
        to="/"
        className="absolute top-6 left-6 z-10 flex items-center gap-2 px-4 py-2 rounded-xl glass text-white/70 hover:text-white transition-colors group"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span className="text-sm font-medium">Back to Home</span>
      </Link>

      {/* Clerk SignIn Component */}
      <div className="relative z-10">
        <SignIn
          routing="path"
          path="/sign-in"
          signUpUrl="/sign-up"
          afterSignInUrl="/app"
          appearance={{
            baseTheme: dark,
            variables: {
              colorPrimary: "#14b8a6", // teal-500
              colorBackground: "#0f0f1a", // midnight-800
              colorInputBackground: "#16161f", // midnight-700
              colorInputText: "white",
              colorText: "white",
              colorTextSecondary: "rgba(255, 255, 255, 0.6)",
              colorDanger: "#f87171",
              borderRadius: "0.75rem",
              fontFamily: "'Inter', system-ui, sans-serif",
            },
            elements: {
              rootBox: "w-full",
              card: "bg-midnight-800/80 backdrop-blur-xl border border-white/10 shadow-2xl",
              headerTitle: "text-white",
              headerSubtitle: "text-white/60",
              socialButtonsBlockButton:
                "bg-white/5 border border-white/10 hover:bg-white/10 transition-colors",
              socialButtonsBlockButtonText: "text-white/80",
              dividerLine: "bg-white/10",
              dividerText: "text-white/40",
              formFieldLabel: "text-white/70",
              formFieldInput:
                "bg-midnight-700 border-white/10 text-white placeholder:text-white/30 focus:border-teal-500 focus:ring-teal-500/20",
              formButtonPrimary:
                "bg-gradient-to-r from-teal-500 to-purple-500 hover:from-teal-400 hover:to-purple-400 shadow-lg shadow-teal-500/20",
              footerActionLink: "text-teal-400 hover:text-teal-300",
              identityPreviewEditButton: "text-teal-400 hover:text-teal-300",
              formResendCodeLink: "text-teal-400 hover:text-teal-300",
              otpCodeFieldInput: "bg-midnight-700 border-white/10 text-white",
              alertText: "text-white/80",
              formFieldSuccessText: "text-teal-400",
            },
          }}
        />
      </div>
    </motion.div>
  );
}
