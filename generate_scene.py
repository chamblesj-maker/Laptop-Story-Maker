"""
Scene Generation Script
Generates prose from scene outlines using LLM
"""

import os
import logging
from typing import Dict, Any, Optional
from . import utils
from .llm_client import LLMManager
from .memory_manager import MemoryManager

logger = logging.getLogger('StoryApp.SceneGen')


class SceneGenerator:
    """Generates prose for scenes"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMManager(config)
        self.memory = MemoryManager(config)

        # Load prompt template
        prompt_path = utils.get_project_path(config, "prompts", "prose_generation_prompt.txt")
        self.prompt_template = utils.load_text_file(prompt_path)

        # Load style guide
        style_path = utils.get_project_path(config, "prompts", "style_guide.md")
        self.style_guide = utils.load_text_file(style_path)

    def generate(self,
                book_name: str,
                chapter: int,
                scene: int,
                scene_outline_path: str,
                save: bool = True) -> Optional[str]:
        """Generate prose for a scene"""

        logger.info(f"Generating Chapter {chapter}, Scene {scene}")

        # Load scene outline
        if not os.path.exists(scene_outline_path):
            logger.error(f"Scene outline not found: {scene_outline_path}")
            return None

        scene_outline = utils.load_text_file(scene_outline_path)

        # Extract metadata from outline
        metadata = self._extract_scene_metadata(scene_outline)

        # Get previous scene summary
        prev_summary = self._get_previous_scene_summary(book_name, chapter, scene)

        # Get continuity context from memory
        continuity = self.memory.get_context_for_scene(
            chapter, scene, scene_outline, book_name
        )

        # Build prompt
        prompt = self._build_prompt(
            book_name=book_name,
            chapter=chapter,
            scene=scene,
            scene_outline=scene_outline,
            previous_summary=prev_summary,
            continuity=continuity,
            metadata=metadata
        )

        # Generate prose
        prose = self._generate_with_validation(prompt, metadata)

        if not prose:
            logger.error("Generation failed")
            return None

        # Save if requested
        if save:
            output_path = utils.get_scene_path(
                self.config, book_name, chapter, scene, "v1", "raw"
            )
            utils.save_text_file(prose, output_path)

            # Generate and save summary
            if self.config['memory']['auto_summarize_scenes']:
                self._generate_and_save_summary(prose, book_name, chapter, scene)

        logger.info(f"Scene generated successfully ({utils.count_words(prose)} words)")
        return prose

    def _extract_scene_metadata(self, outline: str) -> Dict[str, Any]:
        """Extract metadata from scene outline"""
        metadata = {
            'pov_character': 'Unknown',
            'location': 'Unknown',
            'scene_title': 'Untitled',
            'target_word_count': self.config['scene']['target_words']
        }

        # Simple extraction (could be improved with regex)
        for line in outline.split('\n'):
            if 'POV Character:' in line:
                metadata['pov_character'] = line.split(':', 1)[1].strip()
            elif 'Location:' in line or 'Primary Location:' in line:
                metadata['location'] = line.split(':', 1)[1].strip()
            elif 'Scene Title:' in line:
                metadata['scene_title'] = line.split(':', 1)[1].strip()
            elif 'Estimated Word Count:' in line:
                try:
                    wc = line.split(':', 1)[1].strip()
                    metadata['target_word_count'] = int(wc.split()[0])
                except:
                    pass

        return metadata

    def _get_previous_scene_summary(self,
                                   book_name: str,
                                   chapter: int,
                                   scene: int) -> str:
        """Get summary of previous scene"""

        # Check if this is the first scene
        if chapter == 1 and scene == 1:
            return "This is the opening scene of the story."

        # Try to find previous scene summary
        if scene > 1:
            prev_chapter, prev_scene = chapter, scene - 1
        else:
            prev_chapter, prev_scene = chapter - 1, 999  # TODO: get actual last scene of prev chapter

        # TODO: Implement actual summary retrieval from memory or files
        return f"Previous: Chapter {prev_chapter}, Scene {prev_scene}"

    def _build_prompt(self,
                     book_name: str,
                     chapter: int,
                     scene: int,
                     scene_outline: str,
                     previous_summary: str,
                     continuity: str,
                     metadata: Dict[str, Any]) -> str:
        """Build complete generation prompt"""

        # Load story bible summary
        story_bible_path = utils.get_project_path(
            self.config, "story_bible", "story_bible_master.md"
        )
        story_bible = utils.load_text_file(story_bible_path)
        # Take first 2000 words of story bible
        story_bible_summary = ' '.join(story_bible.split()[:2000])

        # Load character bios (TODO: only load relevant characters)
        character_bios = ""  # TODO: Implement character bio loading

        # Get scene config
        scene_cfg = self.config['scene']

        # Format prompt
        prompt = self.prompt_template.format(
            story_title=book_name,
            genre="Fantasy",  # TODO: Get from config
            chapter_number=chapter,
            chapter_title=f"Chapter {chapter}",  # TODO: Get actual title
            story_bible_summary=story_bible_summary,
            character_bios=character_bios,
            retrieved_continuity=continuity,
            previous_scene_summary=previous_summary,
            scene_number=scene,
            scene_title=metadata['scene_title'],
            detailed_scene_outline=scene_outline,
            style_guide_content=self.style_guide,
            target_word_count=metadata['target_word_count'],
            min_words=scene_cfg['min_words'],
            max_words=scene_cfg['max_words'],
            pov_style="third-person limited",  # TODO: Get from config
            tense="past",  # TODO: Get from config
            tone_descriptors="dark, cinematic",  # TODO: Get from config
            pov_character=metadata['pov_character'],
            location=metadata['location']
        )

        return prompt

    def _generate_with_validation(self,
                                  prompt: str,
                                  metadata: Dict[str, Any]) -> Optional[str]:
        """Generate prose with validation"""

        max_retries = self.config['scene']['max_retries']
        scene_cfg = self.config['scene']

        for attempt in range(max_retries):
            logger.info(f"Generation attempt {attempt + 1}/{max_retries}")

            # Generate
            prose = self.llm.generate_with_retry(prompt, 'prose')

            if not prose:
                logger.warning("Empty response from LLM")
                continue

            # Validate word count
            valid, word_count, message = utils.validate_word_count(
                prose,
                metadata['target_word_count'],
                scene_cfg['min_words'],
                scene_cfg['max_words']
            )

            logger.info(message)

            if valid:
                return prose
            else:
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying generation (word count: {word_count})")
                    # Could adjust prompt here to encourage different length
                else:
                    logger.warning(f"Max retries reached. Accepting output despite word count.")
                    return prose

        return None

    def _generate_and_save_summary(self,
                                  prose: str,
                                  book_name: str,
                                  chapter: int,
                                  scene: int):
        """Generate summary and add to memory"""

        summary_length = self.config['memory']['summary_length']

        logger.info("Generating scene summary...")
        summary = self.llm.summarize(prose, max_words=summary_length)

        if summary:
            # Save to memory
            self.memory.add_scene_summary(summary, chapter, scene, book_name)

            # Also save to file
            summary_path = utils.get_scene_path(
                self.config, book_name, chapter, scene, "summary", "raw"
            )
            summary_path = summary_path.replace('.md', '_summary.txt')
            utils.save_text_file(summary, summary_path)

            logger.info("Scene summary saved to memory")


# Standalone function for CLI
def generate_scene_cli(config_path: str,
                      book_name: str,
                      chapter: int,
                      scene: int,
                      outline_path: str):
    """CLI entry point for scene generation"""

    config = utils.load_config(config_path)
    logger = utils.setup_logging(config)

    generator = SceneGenerator(config)

    result = generator.generate(
        book_name=book_name,
        chapter=chapter,
        scene=scene,
        scene_outline_path=outline_path,
        save=True
    )

    if result:
        logger.info("✓ Scene generation complete!")
        return 0
    else:
        logger.error("✗ Scene generation failed")
        return 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: python generate_scene.py <book_name> <chapter> <scene> <outline_path>")
        sys.exit(1)

    book = sys.argv[1]
    ch = int(sys.argv[2])
    sc = int(sys.argv[3])
    outline = sys.argv[4]

    sys.exit(generate_scene_cli("config/config.yaml", book, ch, sc, outline))
