"""
Chapter Assembly Script
Concatenates scenes and applies chapter-level smoothing
"""

import os
import glob
import logging
from typing import Dict, Any, List, Optional
from . import utils
from .llm_client import LLMManager

logger = logging.getLogger('StoryApp.Assembly')


class ChapterAssembler:
    """Assembles scenes into chapters"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMManager(config)

    def assemble(self,
                book_name: str,
                chapter: int,
                scene_paths: Optional[List[str]] = None,
                smooth: bool = True) -> Optional[str]:
        """Assemble chapter from scenes"""

        logger.info(f"Assembling Chapter {chapter}")

        # Get scene paths if not provided
        if scene_paths is None:
            scene_paths = self._discover_scenes(book_name, chapter)

        if not scene_paths:
            logger.error(f"No scenes found for Chapter {chapter}")
            return None

        logger.info(f"Found {len(scene_paths)} scenes")

        # Load and concatenate scenes
        chapter_content = self._concatenate_scenes(scene_paths, chapter)

        if not chapter_content:
            logger.error("Failed to concatenate scenes")
            return None

        # Save raw assembly
        raw_path = utils.get_chapter_path(
            self.config, book_name, chapter, "raw"
        )
        utils.save_text_file(chapter_content, raw_path)

        word_count = utils.count_words(chapter_content)
        logger.info(f"Raw chapter: {word_count} words")

        # Apply smoothing if enabled
        if smooth and self.config['chapter'].get('smoothing_enabled', True):
            smoothed = self._smooth_chapter(chapter_content, chapter)

            if smoothed:
                # Save smoothed version
                smooth_path = utils.get_chapter_path(
                    self.config, book_name, chapter, "v1"
                )
                utils.save_text_file(smoothed, smooth_path)

                smoothed_wc = utils.count_words(smoothed)
                logger.info(f"Smoothed chapter: {smoothed_wc} words")

                return smoothed

        return chapter_content

    def _discover_scenes(self, book_name: str, chapter: int) -> List[str]:
        """Discover all final scenes for a chapter"""

        scenes_dir = utils.get_project_path(
            self.config, "output", book_name, "scenes", "final"
        )

        if not os.path.exists(scenes_dir):
            logger.warning(f"Final scenes directory not found: {scenes_dir}")
            # Try refined directory
            scenes_dir = scenes_dir.replace("final", "refined")

        # Find all scenes for this chapter
        pattern = f"chapter_{chapter:02d}_scene_*_FINAL.md"
        scene_files = glob.glob(os.path.join(scenes_dir, pattern))

        # Sort by scene number
        scene_files.sort()

        logger.debug(f"Discovered scenes: {scene_files}")

        return scene_files

    def _concatenate_scenes(self, scene_paths: List[str], chapter: int) -> str:
        """Concatenate scene files into chapter"""

        parts = [f"# Chapter {chapter}\n\n"]

        for scene_path in scene_paths:
            logger.debug(f"Loading: {scene_path}")

            content = utils.load_text_file(scene_path)

            if not content:
                logger.warning(f"Empty scene file: {scene_path}")
                continue

            # Remove scene header if present
            content = self._remove_scene_header(content)

            parts.append(content)
            parts.append("\n\n---\n\n")  # Scene separator

        # Remove last separator
        if parts and parts[-1].strip() == "---":
            parts.pop()

        return ''.join(parts)

    def _remove_scene_header(self, content: str) -> str:
        """Remove scene metadata header if present"""

        # Remove lines between --- markers at start
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()

        return content

    def _smooth_chapter(self, content: str, chapter: int) -> Optional[str]:
        """Apply chapter-level smoothing pass"""

        logger.info("Applying chapter smoothing pass...")

        prompt = f"""This is a complete chapter assembled from individual scenes.

Review and improve:
1. **Scene-to-scene transitions**: Ensure smooth flow between scenes
2. **Emotional arc**: Check that the chapter has a coherent emotional progression
3. **Pacing consistency**: Ensure pacing doesn't have jarring shifts
4. **Continuity**: Fix any small continuity issues between scenes
5. **Chapter-ending impact**: Ensure the chapter ends with appropriate impact

Make MINIMAL changes to improve flow and coherence. Do not rewrite extensively.
Focus on transitions, pacing, and overall chapter unity.

CHAPTER CONTENT:
{content}

OUTPUT:
Provide the smoothed chapter with improved transitions and flow.
"""

        smoothed = self.llm.generate_with_retry(
            prompt,
            'review',
            temperature=0.7,
            num_predict=len(content.split()) + 500
        )

        if smoothed:
            logger.info("Smoothing complete")
            return smoothed
        else:
            logger.warning("Smoothing failed, using raw assembly")
            return None

    def assemble_book(self, book_name: str, num_chapters: int) -> bool:
        """Assemble all chapters in a book"""

        logger.info(f"Assembling {num_chapters} chapters for: {book_name}")

        progress = utils.ProgressTracker(num_chapters, "Book Assembly")

        for chapter in range(1, num_chapters + 1):
            result = self.assemble(book_name, chapter)

            if result:
                progress.update()
            else:
                logger.error(f"Failed to assemble Chapter {chapter}")

        progress.complete()

        # Create full manuscript
        self._create_manuscript(book_name, num_chapters)

        return True

    def _create_manuscript(self, book_name: str, num_chapters: int):
        """Create full manuscript from all chapters"""

        logger.info("Creating full manuscript...")

        parts = [
            f"# {book_name}\n\n",
            f"*Generated with StoryApp*\n\n",
            "---\n\n"
        ]

        for chapter in range(1, num_chapters + 1):
            chapter_path = utils.get_chapter_path(
                self.config, book_name, chapter, "v1"
            )

            if os.path.exists(chapter_path):
                content = utils.load_text_file(chapter_path)
                parts.append(content)
                parts.append("\n\n")
            else:
                logger.warning(f"Chapter {chapter} not found")

        manuscript = ''.join(parts)

        # Save manuscript
        output_path = utils.get_project_path(
            self.config, "output", book_name, f"{book_name}_manuscript.md"
        )
        utils.save_text_file(manuscript, output_path)

        word_count = utils.count_words(manuscript)
        logger.info(f"Manuscript created: {word_count} words")
        logger.info(f"Saved to: {output_path}")


# CLI Entry Point
def assemble_chapter_cli(config_path: str,
                        book_name: str,
                        chapter: int,
                        smooth: bool = True):
    """CLI entry point for chapter assembly"""

    config = utils.load_config(config_path)
    logger = utils.setup_logging(config)

    assembler = ChapterAssembler(config)

    result = assembler.assemble(book_name, chapter, smooth=smooth)

    if result:
        logger.info("✓ Chapter assembly complete!")
        return 0
    else:
        logger.error("✗ Chapter assembly failed")
        return 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python assemble_chapter.py <book_name> <chapter> [--no-smooth]")
        sys.exit(1)

    book = sys.argv[1]
    ch = int(sys.argv[2])
    smooth = "--no-smooth" not in sys.argv

    sys.exit(assemble_chapter_cli("config/config.yaml", book, ch, smooth))
