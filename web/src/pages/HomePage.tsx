import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchStats, importDeck, Stats } from "../api";

export function HomePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [importPath, setImportPath] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats()
      .then((data) => {
        setStats(data);
        if (data.last_import_path) {
          setImportPath(data.last_import_path);
        }
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleImport() {
    setError(null);
    setMessage(null);
    try {
      const result = await importDeck(importPath);
      setMessage(`Imported ${result.imported} cards from ${result.path}`);
      const updated = await fetchStats();
      setStats(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
  }

  if (loading) {
    return <div className="panel">Loading...</div>;
  }

  return (
    <div className="panel">
      <h1>Deckflow</h1>
      <p className="muted">
        Local-first spaced repetition for git-native markdown decks.
      </p>

      {stats && (
        <div className="stat-grid">
          <div className="stat-card">
            <span className="muted">Due today</span>
            <strong>{stats.due_today}</strong>
          </div>
          <div className="stat-card">
            <span className="muted">Total cards</span>
            <strong>{stats.total_cards}</strong>
          </div>
        </div>
      )}

      <div className="actions">
        <Link className="btn" to="/review">
          Start review
        </Link>
        <Link className="btn secondary" to="/stats">
          View stats
        </Link>
      </div>

      <h2>Import deck</h2>
      <input
        type="text"
        value={importPath}
        onChange={(e) => setImportPath(e.target.value)}
        placeholder="/absolute/path/to/deck.md"
      />
      <div className="actions">
        <button className="btn secondary" onClick={handleImport}>
          Import markdown deck
        </button>
      </div>
      {message && <p>{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
