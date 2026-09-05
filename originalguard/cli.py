"""SHIVANG PLAGCHECK AI CLI.

Allows offline desktop and terminal verification:
- `python -m plagcheck check <file>`
- `python -m plagcheck corpus add <folder_or_file>`
- `python -m plagcheck corpus list`
- `python -m plagcheck report <submission_id>`
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
import click

# Ensure backend is in sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.database import init_db, async_session_maker
from app.models.entities import Submission, Source, Report
from app.schemas.check import CheckOptions
from app.services.corpus.manager import corpus_manager
from app.workers.pipeline_worker import PipelineWorker

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    has_rich = True
    console = Console()
except ImportError:
    has_rich = False
    console = None


@click.group()
def cli():
    """SHIVANG PLAGCHECK AI — Academic Integrity & Similarity Platform."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--offline/--online", default=True, help="Run in local offline mode without external network calls.")
def check(file_path: str, offline: bool):
    """Run originality, AI, and citation check on a PDF, DOCX, or TXT document."""
    async def _run():
        await init_db()
        path = Path(file_path)
        print(f"Processing document: {path.name} ({path.stat().st_size} bytes)...")

        async with async_session_maker() as session:
            await corpus_manager.load_from_db(session)
            # Create submission
            import uuid, hashlib
            with open(path, "rb") as f:
                content = f.read()
            checksum = hashlib.sha256(content).hexdigest()
            sub_id = str(uuid.uuid4())

            sub = Submission(
                id=sub_id,
                title=path.stem,
                original_filename=path.name,
                file_path=str(path.resolve()),
                file_type=path.suffix.lstrip(".").lower(),
                file_size=len(content),
                checksum=checksum,
                status="PENDING",
            )
            session.add(sub)
            await session.commit()

            # Execute pipeline
            worker = PipelineWorker()
            options = CheckOptions(scan_local_corpus=True, scan_external=not offline)
            await worker.execute(session, sub_id, options)

            # Query results
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            stmt = select(Submission).where(Submission.id == sub_id).options(selectinload(Submission.report))
            res = await session.execute(stmt)
            completed_sub = res.scalar_one()
            report = completed_sub.report

            if has_rich:
                table = Table(title=f"SHIVANG PLAGCHECK AI Report — {path.name}", show_header=True, header_style="bold magenta")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="bold white")

                table.add_row("Similarity Index", f"[red]{report.overall_similarity}%[/]")
                table.add_row("Exact Copying", f"{report.exact_similarity}%")
                table.add_row("Near-Verbatim Alignment", f"{report.near_exact_similarity}%")
                table.add_row("Semantic Paraphrasing", f"{report.semantic_similarity}%")
                table.add_row("Estimated AI Likelihood", f"[yellow]{report.ai_likelihood}%[/]")
                table.add_row("Sources Identified", str(report.total_sources))
                table.add_row("Total Analyzed Words", f"{report.total_words:,}")
                table.add_row("Total Pages", str(report.total_pages))
                table.add_row("HTML Report Path", f"[dim]{report.html_path}[/]")
                table.add_row("PDF Report Path", f"[dim]{report.pdf_path}[/]")

                console.print(table)
                console.print(f"\n[green]Check completed successfully![/] ID: [bold]{sub_id}[/]\n")
            else:
                print("\n=======================================================")
                print(f"SHIVANG PLAGCHECK AI Report: {path.name}")
                print("=======================================================")
                print(f"Overall Similarity Index : {report.overall_similarity}%")
                print(f"  - Exact Copying        : {report.exact_similarity}%")
                print(f"  - Near-Verbatim        : {report.near_exact_similarity}%")
                print(f"  - Semantic Paraphrase  : {report.semantic_similarity}%")
                print(f"Estimated AI Likelihood  : {report.ai_likelihood}%")
                print(f"Sources Identified       : {report.total_sources}")
                print(f"Total Words Analyzed     : {report.total_words}")
                print(f"Total Document Pages     : {report.total_pages}")
                print(f"HTML Report Generated    : {report.html_path}")
                print(f"PDF Report Generated     : {report.pdf_path}")
                print("=======================================================")
                print(f"Submission ID: {sub_id}\n")

    asyncio.run(_run())


@cli.group()
def corpus():
    """Corpus management commands."""
    pass


@corpus.command("add")
@click.argument("target_path", type=click.Path(exists=True))
def corpus_add(target_path: str):
    """Index a file or entire directory into the comparison corpus."""
    async def _run():
        await init_db()
        p = Path(target_path)
        files = [p] if p.is_file() else [f for f in p.glob("**/*") if f.suffix.lower() in [".pdf", ".docx", ".txt"]]
        
        print(f"Indexing {len(files)} file(s) into comparison corpus...")

        async with async_session_maker() as session:
            from sqlalchemy import select
            from app.services.document.extractor import DocumentExtractor
            ext = DocumentExtractor()
            added = 0

            for f in files:
                try:
                    doc = ext.extract_file(f)
                    import uuid, hashlib
                    c_sum = hashlib.sha256(doc.raw_text.encode("utf-8")).hexdigest()

                    # Check if already present
                    stmt = select(Source).where(Source.checksum == c_sum)
                    existing = (await session.execute(stmt)).scalar_one_or_none()
                    if existing:
                        corpus_manager.add_document(
                            source_id=existing.id,
                            title=existing.title,
                            text=existing.text,
                        )
                        print(f" [~] Already in corpus: {f.name}")
                        continue

                    src_id = str(uuid.uuid4())
                    # Add to manager and DB
                    corpus_manager.add_document(
                        source_id=src_id,
                        title=f.stem,
                        text=doc.raw_text,
                    )
                    src_row = Source(
                        id=src_id,
                        title=f.stem,
                        checksum=c_sum,
                        text=doc.raw_text,
                    )
                    session.add(src_row)
                    added += 1
                    print(f" [+] Indexed: {f.name} ({doc.word_count} words)")
                except Exception as e:
                    print(f" [!] Error indexing {f.name}: {e}")

            await session.commit()
            print(f"\nSuccessfully indexed {added} new documents into corpus.\n")

    asyncio.run(_run())


@corpus.command("list")
def corpus_list():
    """List all documents in the comparison corpus."""
    async def _run():
        await init_db()
        async with async_session_maker() as session:
            from sqlalchemy import select
            stmt = select(Source)
            res = await session.execute(stmt)
            sources = res.scalars().all()
            print(f"\nCorpus Repository ({len(sources)} documents):")
            print("----------------------------------------------------------------------")
            for s in sources:
                words = len(s.text.split()) if s.text else 0
                print(f" • [{s.id[:8]}] {s.title} ({words} words) - {s.source_type}")
            print("----------------------------------------------------------------------\n")

    asyncio.run(_run())


@cli.command()
@click.argument("submission_id")
def report(submission_id: str):
    """View paths to generated PDF and HTML reports for an analysis run."""
    async def _run():
        await init_db()
        async with async_session_maker() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            stmt = select(Submission).where(Submission.id == submission_id).options(selectinload(Submission.report))
            res = await session.execute(stmt)
            sub = res.scalar_one_or_none()
            if not sub or not sub.report:
                print(f"Report not found for ID: {submission_id}")
                return

            rep = sub.report
            print("\n-----------------------------------------")
            print(f"Originality Report: {sub.title}")
            print(f"Overall Similarity: {rep.overall_similarity}%")
            print(f"AI Likelihood: {rep.ai_likelihood}%")
            print(f"Sources Found: {rep.total_sources}")
            print(f"HTML Report: {rep.html_path}")
            print(f"PDF Report: {rep.pdf_path}")
            print("-----------------------------------------\n")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
