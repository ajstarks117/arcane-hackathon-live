# ARCANE hackathon deployment

Open https://arcane-hackathon-live.vercel.app and sign in with GitHub. Choose **Run repair on a build** to replay the public token-validation regression at `ajstarks117/TEST-REPO@1e690ab`. The worker checks out the broken build, runs the repair graph and Docker tests, and streams node results to the dashboard. PR creation is in dry-run mode. The separate historical merged PR is https://github.com/ajstarks117/TEST-REPO/pull/6.

Vercel serves `new_frontend` and proxies same-origin API requests to the Render origin in `ARCANE_API_URL`. The Render service runs one Uvicorn process using `api.hosted:app`. Render Postgres holds runs, sessions and validated repairs. Each ephemeral worker restores the signed-in user's latest enabled validated repair into ChromaDB. A fresh account starts with empty memory.

The Render Blueprint uses free web and database plans. The web service can sleep between requests. Monitor the database expiry in the Render dashboard if judging continues beyond the free database period.

## Configuration

1. Connect this GitHub repository to the Render Blueprint. Configure the public Vercel origin as `APP_URL` and generate a random 32-byte `WORKER_SECRET`. Set the same secret under GitHub Actions repository secrets alongside `GOOGLE_API_KEY`. Set the Actions repository variable `ARCANE_API_URL` to the Render HTTPS origin.
2. Import `new_frontend` as a Vite project on Vercel. Set its production `ARCANE_API_URL` to the Render origin and deploy.
3. As the repository owner, open `/api/setup/github` on the Vercel site. Register the GitHub App and install it only on this repository. The callback exchanges the single-use manifest code on the backend and persists the app credentials in Postgres. Judges then sign in through the dashboard.
4. Check the signed-out `/api/me` returns 401 and the Render `/health` returns 200. Run a repair, confirm the workflow completes, and inspect the resulting diff and sandbox verdict.

Only the pinned public reproduction is dispatched in this hosted edition. The GitHub App can dispatch the repository's workflow. The runner receives read-only GitHub permissions and the cloud model key. It does not receive user OAuth tokens. The workflow timeout is 40 minutes. Interrupted runs are marked failed by the backend after one hour.
