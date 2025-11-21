"""
Utility functions for StoryApp
"""

import os
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

# Setup logging
def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """Configure logging based on config settings"""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))

    # Create logs directory if it doesn't exist
    log_file = log_config.get('file', 'logs/storyapp.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configure logging
    handlers = []

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    handlers.append(file_handler)

    # Console handler
    if log_config.get('console', True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        handlers.append(console_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )

    return logging.getLogger('StoryApp')


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def save_config(config: Dict[str, Any], config_path: str = "config/config.yaml"):
    """Save configuration to YAML file"""
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)


def ensure_dir(path: str) -> Path:
    """Ensure directory exists, create if not"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def load_text_file(file_path: str) -> str:
    """Load text content from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
        return ""


def save_text_file(content: str, file_path: str):
    """Save text content to file"""
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Saved: {file_path}")


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"JSON file not found: {file_path}")
        return {}


def save_json(data: Dict[str, Any], file_path: str):
    """Save data to JSON file"""
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved JSON: {file_path}")


def count_words(text: str) -> int:
    """Count words in text"""
    # Remove markdown headers, code blocks, etc.
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'---.*?---', '', text, flags=re.DOTALL)

    # Count words
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def format_template(template: str, **kwargs) -> str:
    """Format template string with variables"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logging.error(f"Missing template variable: {e}")
        raise


def get_project_path(config: Dict[str, Any], *parts: str) -> str:
    """Get full path within project"""
    base = config['project']['base_path']
    return os.path.join(base, *parts)


def get_scene_path(config: Dict[str, Any],
                   book_name: str,
                   chapter: int,
                   scene: int,
                   version: str = "v1",
                   stage: str = "raw") -> str:
    """Get path for scene file"""
    base = get_project_path(config, "output", book_name, "scenes", stage)
    filename = f"chapter_{chapter:02d}_scene_{scene:02d}_{version}.md"
    return os.path.join(base, filename)


def get_chapter_path(config: Dict[str, Any],
                     book_name: str,
                     chapter: int,
                     version: str = "v1") -> str:
    """Get path for chapter file"""
    base = get_project_path(config, "output", book_name, "chapters")
    filename = f"chapter_{chapter:02d}_{version}.md"
    return os.path.join(base, filename)


def version_file(file_path: str) -> str:
    """Create versioned filename (v1, v2, v3, etc.)"""
    base, ext = os.path.splitext(file_path)

    # Find highest version number
    version = 1
    while os.path.exists(f"{base}_v{version}{ext}"):
        version += 1

    return f"{base}_v{version}{ext}"


def backup_file(file_path: str, config: Dict[str, Any]) -> Optional[str]:
    """Create backup of file"""
    if not config.get('backup', {}).get('enabled', True):
        return None

    if not os.path.exists(file_path):
        return None

    backup_dir = get_project_path(config, config['backup']['backup_path'])
    ensure_dir(backup_dir)

    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{timestamp}_{basename}")

    import shutil
    shutil.copy2(file_path, backup_path)

    logging.info(f"Backed up: {file_path} -> {backup_path}")
    return backup_path


def extract_metadata(content: str) -> Dict[str, str]:
    """Extract metadata from markdown front matter"""
    metadata = {}

    # Check for YAML front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                pass

    return metadata


def timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize_filename(name: str) -> str:
    """Sanitize string for use as filename"""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    name = name[:100]
    return name


def validate_word_count(text: str,
                       target: int,
                       min_words: int,
                       max_words: int) -> tuple[bool, int, str]:
    """Validate word count is within acceptable range"""
    word_count = count_words(text)

    if word_count < min_words:
        return False, word_count, f"Too short: {word_count} words (min: {min_words})"
    elif word_count > max_words:
        return False, word_count, f"Too long: {word_count} words (max: {max_words})"
    else:
        deviation = abs(word_count - target) / target * 100
        return True, word_count, f"Valid: {word_count} words ({deviation:.1f}% from target)"


def parse_chapter_scene(filename: str) -> tuple[Optional[int], Optional[int]]:
    """Parse chapter and scene numbers from filename"""
    match = re.search(r'chapter_(\d+).*?scene_(\d+)', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def get_latest_version(base_path: str, pattern: str) -> Optional[str]:
    """Get latest version of a file matching pattern"""
    import glob

    files = glob.glob(os.path.join(base_path, pattern))
    if not files:
        return None

    # Sort by modification time
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def create_project_structure(config: Dict[str, Any], book_name: str):
    """Create project directory structure for a new book"""
    base = get_project_path(config, "output", book_name)

    dirs = [
        "scenes/raw",
        "scenes/refined",
        "scenes/final",
        "chapters",
        "images",
        "exports"
    ]

    for d in dirs:
        ensure_dir(os.path.join(base, d))

    logging.info(f"Created project structure for: {book_name}")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


class ProgressTracker:
    """Track and display progress"""

    def __init__(self, total: int, description: str = ""):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()

    def update(self, n: int = 1):
        """Update progress"""
        self.current += n
        self._display()

    def _display(self):
        """Display progress"""
        pct = (self.current / self.total) * 100 if self.total > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = format_duration(eta)
        else:
            eta_str = "Unknown"

        logging.info(
            f"{self.description} Progress: {self.current}/{self.total} "
            f"({pct:.1f}%) - ETA: {eta_str}"
        )

    def complete(self):
        """Mark as complete"""
        self.current = self.total
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logging.info(
            f"{self.description} Complete! "
            f"Total time: {format_duration(elapsed)}"
        )
