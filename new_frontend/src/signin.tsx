import { Button, Mark } from "./ui";

export function SignIn() {
  const err = new URLSearchParams(window.location.search).get("auth_error");
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Mark />
        <span>ARCANE</span>
      </div>
      <div className="auth-card">
        <h1>Welcome to ARCANE</h1>
        <p>Turn broken builds into tested pull requests your team can trust.</p>
        <Button kind="primary" icon="github" onClick={() => (window.location.href = "/api/auth/github/login")}>
          Sign in with GitHub
        </Button>
        {err && <p className="inline-error">GitHub sign-in failed ({err}). Please try again.</p>}
        <small>Sign in to explore three recorded repairs and their pull requests.</small>
      </div>
      <p className="auth-foot">
        <a href="https://github.com/ajstarks117/TEST-REPO/pull/6">View the verified token fix on GitHub</a>
      </p>
    </div>
  );
}
