#!/usr/bin/env python3
"""
StoryApp - AI-Powered Novel Writing System
Main CLI Interface
"""

import os
import sys
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts import utils
from scripts.generate_scene import SceneGenerator
from scripts.refine_scene import SceneRefiner
from scripts.assemble_chapter import ChapterAssembler
from scripts.export import Exporter
from scripts.memory_manager import MemoryManager
from scripts.llm_client import LLMManager

console = Console()

DEFAULT_CONFIG = "config/config.yaml"


@click.group()
@click.option('--config', '-c', default=DEFAULT_CONFIG, help='Config file path')
@click.pass_context
def cli(ctx, config):
    """StoryApp - AI-Powered Novel Writing System"""
    ctx.ensure_object(dict)

    # Load config
    if os.path.exists(config):
        ctx.obj['config'] = utils.load_config(config)
        ctx.obj['logger'] = utils.setup_logging(ctx.obj['config'])
    else:
        console.print(f"[red]Error: Config file not found: {config}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('book_name')
@click.pass_context
def init(ctx, book_name):
    """Initialize a new book project"""
    config = ctx.obj['config']

    console.print(f"[bold]Initializing project: {book_name}[/bold]")

    # Create project structure
    utils.create_project_structure(config, book_name)

    # Update config
    config['project']['name'] = book_name
    utils.save_config(config)

    console.print(f"[green]✓ Project '{book_name}' initialized![/green]")
    console.print("\nNext steps:")
    console.print("1. Fill out story_bible/story_bible_master.md")
    console.print("2. Create character bios in story_bible/character_bios/")
    console.print("3. Generate outlines with: storyapp outline <type>")


@cli.command()
@click.argument('book_name')
@click.argument('chapter', type=int)
@click.argument('scene', type=int)
@click.argument('outline_path')
@click.pass_context
def generate(ctx, book_name, chapter, scene, outline_path):
    """Generate prose for a scene"""
    config = ctx.obj['config']

    console.print(f"[bold]Generating Chapter {chapter}, Scene {scene}[/bold]")

    generator = SceneGenerator(config)

    with console.status("[bold green]Generating with LLM..."):
        result = generator.generate(book_name, chapter, scene, outline_path)

    if result:
        wc = utils.count_words(result)
        console.print(f"[green]✓ Scene generated! ({wc} words)[/green]")
    else:
        console.print("[red]✗ Generation failed[/red]")
        sys.exit(1)


@cli.command()
@click.argument('book_name')
@click.argument('chapter', type=int)
@click.argument('scene', type=int)
@click.option('--input', '-i', 'input_path', required=True, help='Input scene file')
@click.option('--passes', '-p', multiple=True, default=['cohesion', 'style', 'polish'])
@click.pass_context
def refine(ctx, book_name, chapter, scene, input_path, passes):
    """Refine a scene through multiple passes"""
    config = ctx.obj['config']

    console.print(f"[bold]Refining Chapter {chapter}, Scene {scene}[/bold]")
    console.print(f"Passes: {', '.join(passes)}")

    refiner = SceneRefiner(config)

    with console.status("[bold green]Refining..."):
        success = refiner.refine(input_path, book_name, chapter, scene, list(passes))

    if success:
        console.print("[green]✓ Refinement complete![/green]")
    else:
        console.print("[red]✗ Refinement failed[/red]")
        sys.exit(1)


@cli.command()
@click.argument('book_name')
@click.argument('chapter', type=int)
@click.option('--no-smooth', is_flag=True, help='Skip smoothing pass')
@click.pass_context
def assemble(ctx, book_name, chapter, no_smooth):
    """Assemble scenes into a chapter"""
    config = ctx.obj['config']

    console.print(f"[bold]Assembling Chapter {chapter}[/bold]")

    assembler = ChapterAssembler(config)

    with console.status("[bold green]Assembling..."):
        result = assembler.assemble(book_name, chapter, smooth=not no_smooth)

    if result:
        wc = utils.count_words(result)
        console.print(f"[green]✓ Chapter assembled! ({wc} words)[/green]")
    else:
        console.print("[red]✗ Assembly failed[/red]")
        sys.exit(1)


@cli.command()
@click.argument('book_name')
@click.option('--format', '-f', type=click.Choice(['all', 'epub', 'pdf']), default='all')
@click.option('--title', '-t', help='Book title')
@click.option('--author', '-a', help='Author name')
@click.pass_context
def export(ctx, book_name, format, title, author):
    """Export manuscript to various formats"""
    config = ctx.obj['config']

    console.print(f"[bold]Exporting {book_name} to {format}[/bold]")

    exporter = Exporter(config)

    metadata = {}
    if title:
        metadata['title'] = title
    if author:
        metadata['author'] = author

    with console.status("[bold green]Exporting..."):
        if format == 'all':
            results = exporter.export_all(book_name, metadata)
        else:
            manuscript_path = utils.get_project_path(
                config, "output", book_name, f"{book_name}_manuscript.md"
            )

            if format == 'epub':
                results = {'epub': exporter.export_epub(manuscript_path, book_name, metadata)}
            elif format == 'pdf':
                results = {'pdf': exporter.export_pdf(manuscript_path, book_name, metadata)}

    # Display results
    table = Table(title="Export Results")
    table.add_column("Format", style="cyan")
    table.add_column("Status", style="green")

    for fmt, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        style = "green" if success else "red"
        table.add_row(fmt.upper(), f"[{style}]{status}[/{style}]")

    console.print(table)


@cli.command()
@click.argument('book_name')
@click.pass_context
def memory_init(ctx, book_name):
    """Initialize memory system with story bible"""
    config = ctx.obj['config']

    console.print(f"[bold]Initializing memory for: {book_name}[/bold]")

    memory = MemoryManager(config)

    with console.status("[bold green]Loading story bible into memory..."):
        memory.add_story_bible(book_name)

    stats = memory.get_stats()
    console.print(f"[green]✓ Memory initialized![/green]")
    console.print(f"Total entries: {stats.get('total_entries', 0)}")


@cli.command()
@click.pass_context
def check_models(ctx):
    """Check availability of configured LLM models"""
    config = ctx.obj['config']

    console.print("[bold]Checking LLM models...[/bold]")

    llm = LLMManager(config)

    with console.status("[bold green]Querying Ollama..."):
        status = llm.check_models()

    # Display results
    table = Table(title="Model Availability")
    table.add_column("Model", style="cyan")
    table.add_column("Status", style="green")

    for model, available in status.items():
        status_text = "✓ Available" if available else "✗ Not Found"
        style = "green" if available else "red"
        table.add_row(model, f"[{style}]{status_text}[/{style}]")

    console.print(table)

    # Show warning if any missing
    missing = [m for m, avail in status.items() if not avail]
    if missing:
        console.print("\n[yellow]Missing models can be installed with:[/yellow]")
        for model in missing:
            console.print(f"  ollama pull {model}")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration"""
    config = ctx.obj['config']

    console.print("[bold]StoryApp Status[/bold]\n")

    # Project info
    project = config.get('project', {})
    console.print(f"[cyan]Project:[/cyan] {project.get('name', 'Not set')}")
    console.print(f"[cyan]Author:[/cyan] {project.get('author', 'Not set')}")
    console.print(f"[cyan]Base Path:[/cyan] {project.get('base_path', 'Not set')}")

    # LLM info
    console.print(f"\n[bold]LLM Configuration[/bold]")
    models = config.get('models', {})
    console.print(f"[cyan]Prose Model:[/cyan] {models.get('prose', {}).get('primary', 'Not set')}")
    console.print(f"[cyan]Outline Model:[/cyan] {models.get('outline', {}).get('primary', 'Not set')}")

    # Memory info
    memory = MemoryManager(config)
    stats = memory.get_stats()
    console.print(f"\n[bold]Memory System[/bold]")
    console.print(f"[cyan]Database:[/cyan] {stats.get('database_type', 'Not set')}")
    console.print(f"[cyan]Entries:[/cyan] {stats.get('total_entries', 0)}")

    # Export capabilities
    console.print(f"\n[bold]Export Capabilities[/bold]")

    exporter = Exporter(config)
    pandoc_ok = exporter._check_pandoc()

    console.print(f"[cyan]Pandoc:[/cyan] {'✓ Installed' if pandoc_ok else '✗ Not found'}")


@cli.command()
def info():
    """Show information about StoryApp"""

    console.print("[bold cyan]StoryApp - AI-Powered Novel Writing System[/bold cyan]\n")

    console.print("A complete workflow for writing novels with local LLMs.")
    console.print("Optimized for Intel CPU + Arc GPU laptops.\n")

    console.print("[bold]Features:[/bold]")
    console.print("  • Story Bible management")
    console.print("  • Outline-first workflow (Act/Chapter/Scene)")
    console.print("  • LLM-powered prose generation")
    console.print("  • Multi-pass refinement system")
    console.print("  • Vector database for continuity")
    console.print("  • Export to EPUB, PDF, and more\n")

    console.print("[bold]Quick Start:[/bold]")
    console.print("  1. storyapp init <book_name>")
    console.print("  2. Edit story bible and outlines")
    console.print("  3. storyapp generate <book> <ch> <sc> <outline>")
    console.print("  4. storyapp refine <book> <ch> <sc> -i <scene>")
    console.print("  5. storyapp assemble <book> <ch>")
    console.print("  6. storyapp export <book>\n")

    console.print("For full documentation, see README.md")


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == "__main__":
    main()
