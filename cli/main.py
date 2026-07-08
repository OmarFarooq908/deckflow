from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn

from deckflow.compiler.compile import compile_path, write_compiled_output
from deckflow.compiler.migrate import migrate_v1_to_project, scaffold_project
from deckflow.compiler.validator import ValidationError
from deckflow.config import get_db_path
from deckflow.db.repository import Repository
from deckflow.models.domain import LearningLibrary, LibraryNode, ReviewFocus
from deckflow.service.import_service import import_deck
from deckflow.service.library_service import get_learning_library, get_track_focus
from deckflow.service.review_service import get_next_card, submit_review
from deckflow.service.stats_service import get_stats

app = typer.Typer(help="Deckflow — local-first SRS for git-native learning decks")


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


@app.command("init-project")
def init_project_cmd(
    name: str = typer.Argument(..., help="Project name (slug)"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
) -> None:
    """Scaffold a new v2 deck project."""
    project_root = scaffold_project(name, output)
    typer.echo(f"Created deck project at {project_root}")
    typer.echo("Next: edit cards in collections/*/cards/ then run `deckflow validate`")


@app.command("validate")
def validate_cmd(
    path: Path = typer.Argument(..., help="Project, collection dir, or markdown file"),
) -> None:
    """Validate deck project or markdown file."""
    try:
        collections = compile_path(path)
    except (ValidationError, ValueError, FileNotFoundError) as exc:
        typer.echo(f"Validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    total_cards = sum(len(c.cards) for c in collections)
    typer.echo(f"Valid: {len(collections)} collection(s), {total_cards} card(s) — {path.resolve()}")


@app.command("compile")
def compile_cmd(
    path: Path = typer.Argument(..., help="Project, collection dir, or markdown file"),
    output: Path = typer.Option(
        Path(".deckflow/compiled"),
        "--output",
        "-o",
        help="Output directory for compiled JSON",
    ),
) -> None:
    """Compile deck project to JSON artifacts."""
    try:
        collections = compile_path(path)
        written = write_compiled_output(collections, output)
    except (ValidationError, ValueError, FileNotFoundError) as exc:
        typer.echo(f"Compile failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for out_path in written:
        typer.echo(f"Wrote {out_path}")


@app.command("migrate")
def migrate_cmd(
    source: Path = typer.Argument(..., help="v1 markdown deck file"),
    output: Path = typer.Argument(..., help="Output directory for v2 project"),
) -> None:
    """Convert a v1 monolithic markdown deck to a v2 project."""
    try:
        project_root = migrate_v1_to_project(source, output)
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(f"Migration failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Migrated to v2 project at {project_root}")
    typer.echo("Run `deckflow validate` on the project to verify.")


@app.command("import")
def import_cmd(
    path: Path = typer.Argument(
        ...,
        help="Path to v2 project, collection dir, or markdown deck file",
    ),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Import a deck project, collection, or markdown file."""
    repo = _repo(db)
    repo.initialize()
    try:
        result = import_deck(repo, path)
    except (ValidationError, ValueError, FileNotFoundError) as exc:
        typer.echo(f"Import failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Imported {result['imported']} cards across {result['decks']} deck(s) "
        f"({result['format']}) from {result['path']}"
    )


@app.command()
def review(
    limit: int = typer.Option(20, help="Maximum cards to review"),
    deck: str | None = typer.Option(None, "--deck", help="Focus on deck path prefix"),
    topic: str | None = typer.Option(None, "--topic", help="Focus on concept slug"),
    track: str | None = typer.Option(None, "--track", help="Focus on study track step"),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Review due cards in the terminal."""
    repo = _repo(db)
    repo.initialize()

    focus = _resolve_focus(repo, deck=deck, topic=topic, track=track)
    if focus and (focus.deck_prefix or focus.concept_slug):
        label = focus.deck_prefix or focus.concept_slug
        typer.echo(f"Focus: {label}")

    reviewed = 0
    while reviewed < limit:
        card, reason = get_next_card(repo, focus=focus)
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
    by_deck: bool = typer.Option(False, "--by-deck", help="Show per-module deck tree"),
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

    if by_deck:
        typer.echo("")
        typer.echo("Modules (due / total):")
        lib = get_learning_library(repo)
        for node in lib.modules:
            _print_library_node(node, indent=0)


@app.command()
def library(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    db: str | None = typer.Option(None, help="Override database path"),
) -> None:
    """Show the learning library: modules, topics, and study tracks."""
    repo = _repo(db)
    repo.initialize()
    lib = get_learning_library(repo)

    if json_output:
        typer.echo(json.dumps(_library_to_dict(lib), indent=2))
        return

    if lib.collection:
        c = lib.collection
        typer.echo(f"{c.title} — {c.due_count} due · {c.card_count} cards")
        typer.echo("")

    typer.echo("MODULES")
    if not lib.modules:
        typer.echo("  (none)")
    for node in lib.modules:
        _print_library_node(node, indent=1)

    typer.echo("")
    typer.echo("TOPICS")
    if not lib.topics:
        typer.echo("  (none)")
    for node in lib.topics:
        _print_library_node(node, indent=1, show_mastery=True)

    if lib.tracks:
        typer.echo("")
        typer.echo("STUDY TRACKS")
        for track in lib.tracks:
            step_num = track.current_step + 1
            typer.echo(f"  {track.title} — step {step_num} of {track.total_steps}")
            if track.description:
                typer.echo(f"    {track.description}")


def _resolve_focus(
    repo: Repository,
    deck: str | None = None,
    topic: str | None = None,
    track: str | None = None,
) -> ReviewFocus | None:
    if track:
        resolved = get_track_focus(repo, track)
        if resolved:
            return resolved
        typer.echo(f"Unknown track: {track}", err=True)
        raise typer.Exit(code=1)
    if not deck and not topic:
        return None
    return ReviewFocus(deck_prefix=deck, concept_slug=topic)


def _print_library_node(
    node: LibraryNode,
    indent: int = 0,
    show_mastery: bool = False,
) -> None:
    prefix = "  " * indent
    counts = f"{node.due_count} due / {node.card_count} total"
    extra = ""
    if show_mastery and node.mastery_score is not None:
        extra = f" · {node.mastery_score:.0f}%"
    typer.echo(f"{prefix}{node.label}  ({counts}{extra})")
    for child in node.children:
        _print_library_node(child, indent=indent + 1, show_mastery=show_mastery)


def _library_to_dict(lib: LearningLibrary) -> dict[str, object]:
    from dataclasses import asdict

    return asdict(lib)


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
