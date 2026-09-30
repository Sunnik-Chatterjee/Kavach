function readApiBaseUrl(): string {
  const raw = import.meta.env.API_BASE_URL;
  if (!raw) {
    throw new Error(
      "API_BASE_URL is missing. Set it in frontend/.env (see .env.example).",
    );
  }
  return raw.replace(/\/+$/, "");
}

/** Backend origin from env. Never hardcode the host in feature code. */
export const API_BASE_URL = readApiBaseUrl();
