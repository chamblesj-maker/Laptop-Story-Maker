"""
Scene Refinement Script
Multi-pass refinement system for prose
"""

import os
import logging
from typing import Dict, Any, Optional
from . import utils
from .llm_client import LLMManager

logger = logging.getLogger('StoryApp.Refinement')


class SceneRefiner:
    """Multi-pass refinement for scenes"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = LLMManager(config)

        # Load refinement prompts
        prompts_dir = utils.get_project_path(config, "prompts")

        self.prompts = {
            'cohesion': utils.load_text_file(
                os.path.join(prompts_dir, "refinement_pass1_cohesion.txt")
            ),
            'style': utils.load_text_file(
                os.path.join(prompts_dir, "refinement_pass2_style.txt")
            ),
            'polish': utils.load_text_file(
                os.path.join(prompts_dir, "refinement_pass3_polish.txt")
            )
        }

        # Load style guide for pass 2
        self.style_guide = utils.load_text_file(
            os.path.join(prompts_dir, "style_guide.md")
        )

    def refine(self,
              scene_path: str,
              book_name: str,
              chapter: int,
              scene: int,
              passes: Optional[list] = None) -> bool:
        """Run refinement passes on a scene"""

        if passes is None:
            passes = ['cohesion', 'style', 'polish']

        logger.info(f"Refining Chapter {chapter}, Scene {scene}")
        logger.info(f"Passes: {', '.join(passes)}")

        # Load original scene
        if not os.path.exists(scene_path):
            logger.error(f"Scene file not found: {scene_path}")
            return False

        content = utils.load_text_file(scene_path)
        current_content = content

        # Run each pass
        for pass_num, pass_type in enumerate(passes, 1):
            logger.info(f"Running pass {pass_num}/{len(passes)}: {pass_type}")

            refined = self._run_pass(current_content, pass_type)

            if refined:
                # Save intermediate version
                stage = self._get_stage_name(pass_num, len(passes))
                output_path = utils.get_scene_path(
                    self.config, book_name, chapter, scene,
                    f"v{pass_num + 1}_{pass_type}", stage
                )

                utils.save_text_file(refined, output_path)
                current_content = refined

                # Log word count change
                original_wc = utils.count_words(content)
                refined_wc = utils.count_words(refined)
                diff = refined_wc - original_wc
                logger.info(f"Word count: {original_wc} → {refined_wc} ({diff:+d})")
            else:
                logger.error(f"Pass {pass_type} failed")
                return False

        # Save final version
        final_path = utils.get_scene_path(
            self.config, book_name, chapter, scene, "FINAL", "final"
        )
        utils.save_text_file(current_content, final_path)

        logger.info("✓ Refinement complete!")
        return True

    def _run_pass(self, content: str, pass_type: str) -> Optional[str]:
        """Run a single refinement pass"""

        if pass_type not in self.prompts:
            logger.error(f"Unknown pass type: {pass_type}")
            return None

        # Get prompt template
        prompt_template = self.prompts[pass_type]

        # Add style guide for style pass
        if pass_type == 'style':
            prompt_template = prompt_template.replace(
                '{style_guide_content}',
                self.style_guide
            )

        # Generate refined version
        refined = self.llm.refine_scene(
            prompt_template,
            content,
            pass_type
        )

        return refined

    def _get_stage_name(self, pass_num: int, total_passes: int) -> str:
        """Get stage name based on pass number"""
        if pass_num < total_passes:
            return "refined"
        else:
            return "final"

    def refine_chapter(self,
                      book_name: str,
                      chapter: int,
                      num_scenes: int) -> bool:
        """Refine all scenes in a chapter"""

        logger.info(f"Refining all scenes in Chapter {chapter}")

        success_count = 0

        for scene in range(1, num_scenes + 1):
            # Get raw scene path
            scene_path = utils.get_scene_path(
                self.config, book_name, chapter, scene, "v1", "raw"
            )

            if not os.path.exists(scene_path):
                logger.warning(f"Scene {scene} not found, skipping")
                continue

            success = self.refine(scene_path, book_name, chapter, scene)

            if success:
                success_count += 1

        logger.info(f"Refined {success_count}/{num_scenes} scenes")
        return success_count == num_scenes


class BatchRefiner:
    """Batch refinement for multiple scenes"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.refiner = SceneRefiner(config)

    def refine_book(self, book_name: str) -> bool:
        """Refine entire book"""

        logger.info(f"Starting batch refinement for: {book_name}")

        # TODO: Discover all scenes automatically
        # For now, this is a placeholder

        logger.info("Batch refinement complete")
        return True

    def refine_from_list(self, scene_list_path: str) -> bool:
        """Refine scenes from a list file"""

        # Load scene list
        with open(scene_list_path, 'r') as f:
            scenes = [line.strip().split(',') for line in f if line.strip()]

        total = len(scenes)
        progress = utils.ProgressTracker(total, "Batch Refinement")

        for book, chapter, scene, path in scenes:
            self.refiner.refine(
                path,
                book,
                int(chapter),
                int(scene)
            )
            progress.update()

        progress.complete()
        return True


# CLI Entry Point
def refine_scene_cli(config_path: str,
                    book_name: str,
                    chapter: int,
                    scene: int,
                    scene_path: str):
    """CLI entry point for scene refinement"""

    config = utils.load_config(config_path)
    logger = utils.setup_logging(config)

    refiner = SceneRefiner(config)

    success = refiner.refine(scene_path, book_name, chapter, scene)

    if success:
        logger.info("✓ Refinement complete!")
        return 0
    else:
        logger.error("✗ Refinement failed")
        return 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: python refine_scene.py <book_name> <chapter> <scene> <scene_path>")
        sys.exit(1)

    book = sys.argv[1]
    ch = int(sys.argv[2])
    sc = int(sys.argv[3])
    path = sys.argv[4]

    sys.exit(refine_scene_cli("config/config.yaml", book, ch, sc, path))
