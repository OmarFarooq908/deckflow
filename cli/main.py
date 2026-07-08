from __future__ import annotations

from pathlib import Path

import typer
import uvicorn

from deckflow.config import get_db_path
from deckflow.db.repository import Repository
from deckflow.service.import_service import import_deck
from deckflow.service.review_service import get_next_card, submit_review
from deckflow.service.stats_service import get_stats

app = typer.Typer(help="Deckflow — local-first SRS for git-native markdown decks")


def _repo(db: str | None) -> Repository:
    return Repository(get_db_path(db))


@app.command()
def init(
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Create the local database and config directory."""
    repo = _repo(db)
    repo.initialize()
    typer.echo(f"Initialized database at {repo.db_path}")


@app.command("import")
def import_cmd(
    path: Path = typer.Argument(..., help="Path to markdown deck file"),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Import a markdown deck file."""
    repo = _repo(db)
    repo.initialize()
    result = import_deck(repo, path)
    typer.echo(
        f"Imported {result['imported']} cards across {result['decks']} deck(s) "
        f"from {result['path']}"
    )


@app.command()
def review(
    limit: int = typer.Option(20, help="Maximum cards to review"),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Review due cards in the terminal."""
    repo = _repo(db)
    repo.initialize()

    reviewed = 0
    while reviewed < limit:
        card, reason = get_next_card(repo)
        if card is None:
            if reviewed == 0:
                typer.echo("No cards due for review.")
            else:
                typer.echo(f"Review session complete. Reviewed {reviewed} card(s).")
            return

        typer.echo("\n" + "=" * 60)
        typer.echo(f"Deck: {card.deck_path}")
        if reason:
            typer.echo(f"Queue: {reason}")
        if card.hint:
            typer.echo(f"Hint: {card.hint}")
        if card.tags:
            typer.echo(f"Tags: {', '.join(card.tags)}")
        typer.echo("-" * 60)
        typer.echo("FRONT:")
        typer.echo(card.front_md)
        typer.echo("-" * 60)

        if not typer.confirm("Reveal answer?", default=True):
            typer.echo("Skipped.")
            continue

        typer.echo("BACK:")
        typer.echo(card.back_md)
        typer.echo("-" * 60)
        typer.echo("Rate: 1=Again  2=Hard  3=Good  4=Easy")
        rating = typer.prompt("Your rating", type=int)
        while rating not in (1, 2, 3, 4):
            rating = typer.prompt("Enter 1-4", type=int)

        submit_review(repo, card.id, rating)
        reviewed += 1
        typer.echo("Saved.")

    typer.echo(f"Review session complete. Reviewed {reviewed} card(s).")


@app.command()
def stats(
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Show review statistics."""
    repo = _repo(db)
    repo.initialize()
    s = get_stats(repo)
    typer.echo(f"Due today:       {s.due_today}")
    typer.echo(f"New cards:       {s.new_cards}")
    typer.echo(f"Reviewed today:  {s.reviewed_today}")
    typer.echo(f"Total cards:     {s.total_cards}")
    typer.echo(f"Retention:       {s.retention_pct}%")
    typer.echo(f"Streak:          {s.streak_days} day(s)")


@app.command()
def serve(
    port: int = typer.Option(5174, help="API port"),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Start the FastAPI server for the web UI."""
    import os

    if db:
        os.environ["DECKFLOW_DB"] = db
    repo = _repo(db)
    repo.initialize()
    typer.echo(f"Serving API at http://localhost:{port} (db: {repo.db_path})")
    uvicorn.run("api.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    app()
