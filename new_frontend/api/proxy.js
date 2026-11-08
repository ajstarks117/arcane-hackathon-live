// Keep GitHub OAuth cookies on the dashboard's origin; only forward to the configured API.
export default async function handler(req, res) {
  res.setHeader("Cache-Control", "private, no-store");
  const origin = process.env.ARCANE_API_URL;
  if (!origin) return res.status(503).json({detail: "The dashboard API is awaiting deployment."});
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(req.query)) {
    if (key === "route") continue;
    for (const item of [].concat(value)) query.append(key, item);
  }
  const route = req.query.route;
  if (typeof route !== "string" || !/^[a-zA-Z0-9_/-]+$/.test(route))
    return res.status(400).end();
  query.delete("route");
  const target = new URL("/api/" + route, origin);
  target.search = query.toString();
  const headers = {};
  for (const key of ["cookie", "content-type", "accept"])
    if (req.headers[key]) headers[key] = req.headers[key];
  const options = {method: req.method, headers, redirect: "manual"};
  if (!["GET", "HEAD"].includes(req.method) && req.body != null)
    options.body = typeof req.body === "string" || Buffer.isBuffer(req.body) ? req.body : JSON.stringify(req.body);
  try {
    const response = await fetch(target, options);
    for (const key of ["content-type", "location"])
      if (response.headers.has(key)) res.setHeader(key, response.headers.get(key));
    const cookies = response.headers.getSetCookie();
    if (cookies.length) res.setHeader("Set-Cookie", cookies);
    res.status(response.status).send(Buffer.from(await response.arrayBuffer()));
  } catch {
    res.status(502).json({detail: "Could not reach the repair API. Please retry."});
  }
}
