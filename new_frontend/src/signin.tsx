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
        <small>You will choose which of your repositories ARCANE may watch after signing in.</small>
      </div>
      <p className="auth-foot">
        ARCANE asks for repository access so it can read failing files, open pull requests and create the push webhook.
      </p>
    </div>
  );
}
