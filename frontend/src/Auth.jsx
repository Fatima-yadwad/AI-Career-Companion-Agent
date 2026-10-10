import { useState } from "react";
import "./Auth.css";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

export default function Auth({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const isSignup = mode === "signup";

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
    setConfirmPassword("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (isSignup && !fullName.trim()) {
      setError("Please enter your full name.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    if (isSignup && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const endpoint = isSignup
        ? "/auth/register"
        : "/auth/login";

      const payload = isSignup
        ? {
            full_name: fullName.trim(),
            email: email.trim(),
            password,
            confirm_password: confirmPassword,
          }
        : {
            email: email.trim(),
            password,
          };

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = data.detail;
        const message = Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : typeof detail === "string"
            ? detail
            : data.message;

        throw new Error(
          message || "Authentication failed. Please try again."
        );
      }

      if (!data.token) {
        throw new Error(
          "The server did not return an authentication token."
        );
      }

      // Store the session for the later dashboard integration.
      localStorage.setItem("career_auth_token", data.token);

      if (data.user) {
        localStorage.setItem(
          "career_auth_user",
          JSON.stringify(data.user)
        );
      }

      const profile = data.profile;
      const profileId =
        profile?.profile_id ??
        profile?.id ??
        data.user?.profile_id;

      if (profileId !== undefined && profileId !== null) {
        localStorage.setItem(
          "career_profile_id",
          String(profileId)
        );
      }

      setSuccess(
        data.message ||
          (isSignup
            ? "Account created successfully!"
            : "Login successful!")
      );

      if (typeof onAuthSuccess === "function") {
        onAuthSuccess(data);
      }
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the server. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-visual">
        <div className="auth-brand">
          <div className="auth-brand-icon">C</div>
          <span>Career Companion</span>
        </div>

        <div className="auth-hero">
          <span className="auth-eyebrow">
            YOUR CAREER, YOUR FUTURE
          </span>

          <h1>
            Build your future.
            <br />
            <span>One step at a time.</span>
          </h1>

          <p>
            Organize your job search, identify skill gaps,
            prepare for interviews, and move closer to your
            career goals.
          </p>

          <div className="auth-feature-list">
            <div>
              <span className="auth-check">✓</span>
              Personalized career insights
            </div>
            <div>
              <span className="auth-check">✓</span>
              Resume and job application tracking
            </div>
            <div>
              <span className="auth-check">✓</span>
              Interview preparation and AI assistance
            </div>
          </div>
        </div>

        <div className="auth-visual-footer">
          AI Career Companion Agent
        </div>
      </section>

      <section className="auth-form-section">
        <div className="auth-form-card">
          <div className="auth-mobile-brand">
            <div className="auth-brand-icon">C</div>
            <span>Career Companion</span>
          </div>

          <div className="auth-form-heading">
            <span className="auth-form-kicker">
              {isSignup ? "GET STARTED" : "WELCOME BACK"}
            </span>

            <h2>
              {isSignup
                ? "Create your account"
                : "Welcome back!"}
            </h2>

            <p>
              {isSignup
                ? "Start building your career journey today."
                : "Sign in to continue your career journey."}
            </p>
          </div>

          <div className="auth-tabs">
            <button
              type="button"
              className={!isSignup ? "active" : ""}
              onClick={() => switchMode("login")}
            >
              Login
            </button>

            <button
              type="button"
              className={isSignup ? "active" : ""}
              onClick={() => switchMode("signup")}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {isSignup && (
              <div className="auth-field">
                <label htmlFor="auth-full-name">Full name</label>
                <input
                  id="auth-full-name"
                  type="text"
                  placeholder="Enter your full name"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  required
                />
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="auth-email">Email address</label>
              <input
                id="auth-email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                required
              />
            </div>

            <div className="auth-field">
              <label htmlFor="auth-password">Password</label>

              <div className="auth-password-wrapper">
                <input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="At least 8 characters"
                  autoComplete={
                    isSignup
                      ? "new-password"
                      : "current-password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  minLength={8}
                  required
                />

                <button
                  type="button"
                  className="auth-show-password"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            {isSignup && (
              <div className="auth-field">
                <label htmlFor="auth-confirm-password">
                  Confirm password
                </label>
                <input
                  id="auth-confirm-password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password again"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  required
                />
              </div>
            )}

            {error && (
              <div className="auth-message auth-error" role="alert">
                {error}
              </div>
            )}

            {success && (
              <div
                className="auth-message auth-success"
                role="status"
              >
                {success}
              </div>
            )}

            <button
              type="submit"
              className="auth-submit"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : isSignup
                  ? "Create Account"
                  : "Login to Dashboard"}

              {!loading && <span aria-hidden="true"> →</span>}
            </button>
          </form>

          <p className="auth-switch-text">
            {isSignup
              ? "Already have an account?"
              : "New to Career Companion?"}{" "}
            <button
              type="button"
              onClick={() =>
                switchMode(isSignup ? "login" : "signup")
              }
            >
              {isSignup ? "Login" : "Create an account"}
            </button>
          </p>

          <p className="auth-privacy-note">
            Your career journey starts here.
          </p>
        </div>
      </section>
    </main>
  );
}
