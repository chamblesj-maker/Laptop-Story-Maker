"""
Export Script - Convert manuscript to various formats
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional
from . import utils

logger = logging.getLogger('StoryApp.Export')


class Exporter:
    """Export manuscript to various formats"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.export_config = config.get('export', {})

    def export_epub(self,
                   manuscript_path: str,
                   book_name: str,
                   metadata: Optional[Dict[str, str]] = None) -> bool:
        """Export to EPUB format using Pandoc"""

        if not self.export_config.get('formats', {}).get('epub', {}).get('enabled', True):
            logger.info("EPUB export disabled in config")
            return False

        logger.info("Exporting to EPUB...")

        if not os.path.exists(manuscript_path):
            logger.error(f"Manuscript not found: {manuscript_path}")
            return False

        # Check if pandoc is installed
        if not self._check_pandoc():
            logger.error("Pandoc not installed. Install from: https://pandoc.org")
            return False

        # Prepare output path
        output_dir = utils.get_project_path(self.config, "output", book_name, "exports")
        utils.ensure_dir(output_dir)
        output_file = os.path.join(output_dir, f"{book_name}.epub")

        # Build pandoc command
        cmd = [
            "pandoc",
            manuscript_path,
            "-o", output_file,
            "--toc",  # Table of contents
            "--toc-depth=2"
        ]

        # Add metadata
        if metadata:
            if 'title' in metadata:
                cmd.extend(["--metadata", f"title={metadata['title']}"])
            if 'author' in metadata:
                cmd.extend(["--metadata", f"author={metadata['author']}"])

        # Add cover if exists
        cover_path = os.path.join(output_dir, "cover.jpg")
        if os.path.exists(cover_path):
            cmd.append(f"--epub-cover-image={cover_path}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"✓ EPUB created: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc failed: {e.stderr}")
            return False

    def export_pdf(self,
                  manuscript_path: str,
                  book_name: str,
                  metadata: Optional[Dict[str, str]] = None) -> bool:
        """Export to PDF format using Pandoc"""

        if not self.export_config.get('formats', {}).get('pdf', {}).get('enabled', True):
            logger.info("PDF export disabled in config")
            return False

        logger.info("Exporting to PDF...")

        if not os.path.exists(manuscript_path):
            logger.error(f"Manuscript not found: {manuscript_path}")
            return False

        # Check if pandoc is installed
        if not self._check_pandoc():
            logger.error("Pandoc not installed")
            return False

        # Prepare output path
        output_dir = utils.get_project_path(self.config, "output", book_name, "exports")
        utils.ensure_dir(output_dir)
        output_file = os.path.join(output_dir, f"{book_name}.pdf")

        # Get PDF config
        pdf_cfg = self.export_config.get('formats', {}).get('pdf', {})
        engine = pdf_cfg.get('engine', 'xelatex')
        font_size = pdf_cfg.get('font_size', 12)
        margin = pdf_cfg.get('margin', '1in')

        # Build pandoc command
        cmd = [
            "pandoc",
            manuscript_path,
            "-o", output_file,
            f"--pdf-engine={engine}",
            f"--variable=fontsize={font_size}pt",
            f"--variable=geometry:margin={margin}"
        ]

        # Add metadata
        if metadata:
            if 'title' in metadata:
                cmd.extend(["--metadata", f"title={metadata['title']}"])
            if 'author' in metadata:
                cmd.extend(["--metadata", f"author={metadata['author']}"])

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"✓ PDF created: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc failed: {e.stderr}")
            logger.error(f"Make sure {engine} is installed")
            return False

    def export_audiobook(self,
                        manuscript_path: str,
                        book_name: str) -> bool:
        """Export to audiobook using TTS"""

        if not self.export_config.get('formats', {}).get('audiobook', {}).get('enabled', False):
            logger.info("Audiobook export disabled in config")
            return False

        logger.info("Audiobook export not yet implemented")
        logger.info("Planned: Use Piper/Kokoro TTS to generate audio")

        # TODO: Implement audiobook generation
        # 1. Split manuscript by chapters
        # 2. Generate audio for each chapter with Piper/Kokoro
        # 3. Normalize audio levels
        # 4. Add chapter markers
        # 5. Compile to M4B format

        return False

    def export_all(self,
                  book_name: str,
                  metadata: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """Export to all enabled formats"""

        manuscript_path = utils.get_project_path(
            self.config, "output", book_name, f"{book_name}_manuscript.md"
        )

        if not os.path.exists(manuscript_path):
            logger.error(f"Manuscript not found: {manuscript_path}")
            return {}

        results = {}

        # EPUB
        if self.export_config.get('formats', {}).get('epub', {}).get('enabled', True):
            results['epub'] = self.export_epub(manuscript_path, book_name, metadata)

        # PDF
        if self.export_config.get('formats', {}).get('pdf', {}).get('enabled', True):
            results['pdf'] = self.export_pdf(manuscript_path, book_name, metadata)

        # Audiobook
        if self.export_config.get('formats', {}).get('audiobook', {}).get('enabled', False):
            results['audiobook'] = self.export_audiobook(manuscript_path, book_name)

        return results

    def _check_pandoc(self) -> bool:
        """Check if Pandoc is installed"""
        try:
            subprocess.run(["pandoc", "--version"],
                         capture_output=True,
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


# CLI Entry Point
def export_cli(config_path: str,
              book_name: str,
              format: str = "all",
              title: Optional[str] = None,
              author: Optional[str] = None):
    """CLI entry point for export"""

    config = utils.load_config(config_path)
    logger = utils.setup_logging(config)

    exporter = Exporter(config)

    metadata = {}
    if title:
        metadata['title'] = title
    if author:
        metadata['author'] = author

    if format == "all":
        results = exporter.export_all(book_name, metadata)

        logger.info("\nExport Results:")
        for fmt, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {fmt.upper()}")

        return 0 if all(results.values()) else 1

    elif format == "epub":
        manuscript_path = utils.get_project_path(
            config, "output", book_name, f"{book_name}_manuscript.md"
        )
        success = exporter.export_epub(manuscript_path, book_name, metadata)
        return 0 if success else 1

    elif format == "pdf":
        manuscript_path = utils.get_project_path(
            config, "output", book_name, f"{book_name}_manuscript.md"
        )
        success = exporter.export_pdf(manuscript_path, book_name, metadata)
        return 0 if success else 1

    else:
        logger.error(f"Unknown format: {format}")
        return 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python export.py <book_name> [format] [--title TITLE] [--author AUTHOR]")
        print("Formats: all, epub, pdf")
        sys.exit(1)

    book = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "all"

    # Parse optional args
    title = None
    author = None

    for i, arg in enumerate(sys.argv):
        if arg == "--title" and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
        elif arg == "--author" and i + 1 < len(sys.argv):
            author = sys.argv[i + 1]

    sys.exit(export_cli("config/config.yaml", book, fmt, title, author))
