export function formatApiError(error: unknown): string {
  const message = error instanceof Error ? error.message : "Something went wrong";

  if (message.includes("Not Found") || message.includes("404")) {
    return "This feature needs a newer API. Restart with `deckflow serve`, then open http://localhost:5173 (not 5174).";
  }

  if (message.includes("API unreachable")) {
    return message;
  }

  if (message.startsWith("{")) {
    try {
      const parsed = JSON.parse(message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // fall through
    }
  }

  return message;
}

export function greetingForHour(hour: number): string {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function parseDeckPath(path: string): string[] {
  return path.split("::").filter(Boolean);
}

export function reviewUrl(
  deck?: string | null,
  concept?: string | null,
  track?: string | null,
): string {
  const params = new URLSearchParams();
  if (deck) params.set("deck", deck);
  if (concept) params.set("concept", concept);
  if (track) params.set("track", track);
  const query = params.toString();
  return query ? `/review?${query}` : "/review";
}
