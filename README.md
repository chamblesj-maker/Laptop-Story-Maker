# StoryApp - AI-Powered Novel Writing System

A complete, local LLM-powered workflow for writing novels with an outline-first methodology. Optimized for Intel CPU + Arc GPU laptops.

## Features

- **Story Bible Management**: Comprehensive templates for world-building, characters, and continuity
- **Outline-First Workflow**: Three-layer outlining (Act → Chapter → Scene)
- **LLM-Powered Generation**: Uses local models via Ollama for complete privacy
- **Multi-Pass Refinement**: Automated cohesion, style, and polish passes
- **Vector Database Memory**: Maintains continuity across scenes using ChromaDB
- **Export Pipeline**: Generate EPUB, PDF, and audiobook formats
- **Intel Arc Optimized**: Configured for optimal performance on Intel GPUs

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Workflow](#workflow)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

1. **Python 3.9+**
2. **Ollama** (for LLM inference)
3. **Pandoc** (for export features)
4. **Optional**: XeLaTeX or PDFLaTeX (for PDF export)

### Step 1: Install Ollama

```bash
# Windows: Download from https://ollama.com
# Linux/Mac:
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Pull LLM Models

```bash
# Core models
ollama pull llama3:8b
ollama pull gemma2:9b
ollama pull phi4:latest
ollama pull deepseek-r1:14b
ollama pull mistral-nemo:12b

# Optional: Heavy model for desktop server
ollama pull llama3:70b
```

### Step 3: Install StoryApp

```bash
cd "C:\Users\chamb\AI-ML Projects\StoryApp"

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install in development mode
pip install -e .
```

### Step 4: Install Pandoc (for export)

- **Windows**: Download from https://pandoc.org/installing.html
- **Linux**: `sudo apt install pandoc texlive-xetex` (includes XeLaTeX)
- **Mac**: `brew install pandoc basictex`

### Step 5: Verify Installation

```bash
python storyapp.py check-models
```

## Quick Start

### 1. Initialize a New Book

```bash
python storyapp.py init "MyNovel"
```

This creates:
- Project folder structure
- Story bible templates
- Configuration

### 2. Fill Out Story Bible

Edit these files in `story_bible/`:

- `story_bible_master.md` - Core story information
- `world_summary.md` - World-building details
- `magic_tech_systems.md` - Rules and systems
- `character_bios/protagonist.md` - Character profiles
- `timeline.md` - Story chronology

### 3. Create Outlines

Use the templates in `prompts/`:

```bash
# Create Act outline
# Edit: prompts/act_outline_template.md → outlines/MyNovel/act_structure.md

# Create Chapter outlines
# Edit: prompts/chapter_outline_template.md → outlines/MyNovel/chapters/chapter_01_outline.md

# Create Scene outlines
# Edit: prompts/scene_outline_template.md → outlines/MyNovel/scenes/chapter_01_scene_01.md
```

### 4. Initialize Memory System

```bash
python storyapp.py memory-init "MyNovel"
```

### 5. Generate Your First Scene

```bash
python storyapp.py generate "MyNovel" 1 1 "outlines/MyNovel/scenes/chapter_01_scene_01.md"
```

### 6. Refine the Scene

```bash
python storyapp.py refine "MyNovel" 1 1 -i "output/MyNovel/scenes/raw/chapter_01_scene_01_v1.md"
```

### 7. Generate More Scenes

Repeat steps 5-6 for all scenes in the chapter.

### 8. Assemble Chapter

```bash
python storyapp.py assemble "MyNovel" 1
```

### 9. Export

```bash
python storyapp.py export "MyNovel" --title "My Novel" --author "Your Name"
```

## Workflow

### Complete Novel Writing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. STORY BIBLE CREATION                                     │
│    Fill out templates in story_bible/                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. OUTLINING (Outline-First!)                               │
│    A. Three-Act Structure                                   │
│    B. Chapter Outlines (all chapters)                       │
│    C. Scene Outlines (all scenes)                           │
│    Lock outlines before proceeding                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PROSE GENERATION (Scene by Scene)                        │
│    python storyapp.py generate <book> <ch> <sc> <outline>   │
│    → Generates 1,200-1,800 word scenes                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. MULTI-PASS REFINEMENT                                    │
│    python storyapp.py refine <book> <ch> <sc> -i <file>     │
│    → Pass 1: Cohesion & Flow                                │
│    → Pass 2: Voice & Style                                  │
│    → Pass 3: Error Correction & Polish                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CHAPTER ASSEMBLY                                         │
│    python storyapp.py assemble <book> <chapter>             │
│    → Concatenates scenes + smoothing pass                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. EXPORT                                                   │
│    python storyapp.py export <book>                         │
│    → EPUB, PDF, (Audiobook planned)                         │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Main Config File: `config/config.yaml`

#### Key Settings

**Project Settings**
```yaml
project:
  name: "MyNovel"
  author: "Your Name"
  base_path: "C:/Users/chamb/AI-ML Projects/StoryApp"
```

**Model Selection**
```yaml
models:
  prose:
    primary: "gemma2:9b"    # Creative prose generation
  outline:
    primary: "deepseek-r1:14b"  # Reasoning for outlines
  refinement:
    style: "gemma2:9b"      # Style enforcement
```

**Generation Parameters**
```yaml
generation:
  prose:
    temperature: 0.85       # Higher = more creative
    top_p: 0.9
    repeat_penalty: 1.15    # Reduces repetition
```

**Scene Settings**
```yaml
scene:
  target_words: 1500
  min_words: 1200
  max_words: 1800
```

## CLI Reference

### Core Commands

#### `init`
Initialize a new book project

```bash
python storyapp.py init <book_name>
```

#### `generate`
Generate prose for a scene

```bash
python storyapp.py generate <book_name> <chapter> <scene> <outline_path>

# Example:
python storyapp.py generate "MyNovel" 1 1 "outlines/MyNovel/scenes/ch01_sc01.md"
```

#### `refine`
Refine a scene through multiple passes

```bash
python storyapp.py refine <book_name> <chapter> <scene> -i <input_path>

# With specific passes:
python storyapp.py refine "MyNovel" 1 1 -i scene.md --passes cohesion --passes style

# Available passes: cohesion, style, polish
```

#### `assemble`
Assemble scenes into a chapter

```bash
python storyapp.py assemble <book_name> <chapter>

# Skip smoothing:
python storyapp.py assemble "MyNovel" 1 --no-smooth
```

#### `export`
Export manuscript to various formats

```bash
# Export all formats:
python storyapp.py export "MyNovel" --title "My Novel" --author "John Doe"

# Export specific format:
python storyapp.py export "MyNovel" --format epub
python storyapp.py export "MyNovel" --format pdf
```

#### `memory-init`
Initialize memory system with story bible

```bash
python storyapp.py memory-init "MyNovel"
```

#### `check-models`
Check availability of configured LLM models

```bash
python storyapp.py check-models
```

#### `status`
Show system status and configuration

```bash
python storyapp.py status
```

#### `info`
Show information about StoryApp

```bash
python storyapp.py info
```

## Advanced Usage

### Custom Style Guide

Edit `prompts/style_guide.md` to define your unique prose style:

- Narrative voice
- Sentence structure preferences
- Dialogue style
- Descriptive approach
- Pacing guidelines

### Memory System

The vector database maintains continuity by tracking:

- Character descriptions
- World rules
- Previous scene events
- Continuity details

**Adding Custom Continuity Notes:**

```python
from scripts.memory_manager import MemoryManager
from scripts.utils import load_config

config = load_config()
memory = MemoryManager(config)

memory.add_continuity_note(
    "The magic sword is silver with blue runes, not gold",
    category="items",
    book_name="MyNovel"
)
```

### Batch Processing

Create a batch script for multiple scenes:

```python
# batch_generate.py
from scripts.generate_scene import SceneGenerator
from scripts.utils import load_config

config = load_config()
generator = SceneGenerator(config)

scenes = [
    (1, 1, "outlines/MyNovel/scenes/ch01_sc01.md"),
    (1, 2, "outlines/MyNovel/scenes/ch01_sc02.md"),
    (1, 3, "outlines/MyNovel/scenes/ch01_sc03.md"),
]

for ch, sc, outline in scenes:
    generator.generate("MyNovel", ch, sc, outline)
```

### Using Remote LLM Server

For heavy models on a separate machine:

```yaml
# config/config.yaml
models:
  prose:
    primary: "llama3:70b"
    server: "http://192.168.1.100:11434"  # Remote server
```

### Intel Arc GPU Optimization

**Ensure Latest Drivers**:
- Download from: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-windows.html

**Ollama with Intel GPU**:
```bash
# Ollama should automatically detect Intel Arc GPU
# Verify with:
ollama list
nvidia-smi  # Won't work for Arc, use:
# Check Task Manager → Performance → GPU
```

**Model Quantization**:
- Use Q4_K_M quantized models for best performance
- Example: `llama3:8b-q4_K_M`

## Troubleshooting

### Common Issues

**1. "Model not found" error**

```bash
# Pull the model:
ollama pull gemma2:9b
```

**2. Generation is too slow**

- Use smaller models (8B instead of 70B)
- Reduce `num_ctx` in config
- Use quantized models (Q4_K_M)

**3. Word count validation fails**

- Adjust `min_words` and `max_words` in config
- Increase `max_retries` for scene generation
- Check prompt length (too long prompts reduce output)

**4. "Pandoc not found" during export**

```bash
# Install Pandoc:
# Windows: https://pandoc.org/installing.html
# Linux: sudo apt install pandoc
```

**5. Memory/Continuity errors**

```bash
# Re-initialize memory:
python storyapp.py memory-init "MyNovel"
```

**6. Python import errors**

```bash
# Reinstall dependencies:
pip install -r requirements.txt --upgrade
```

### Performance Optimization

**For Intel Arc GPU**:

1. Use INT4/INT8 quantized models
2. Limit context window to 8192 tokens
3. Set appropriate `num_predict` based on desired output length
4. Monitor VRAM usage (8-10GB max for 12B models)

**For Faster Generation**:

```yaml
# config/config.yaml
generation:
  prose:
    temperature: 0.85
    num_predict: 1800     # Match target word count
    num_ctx: 4096         # Reduce if slow
```

## Project Structure

```
StoryApp/
├── config/
│   └── config.yaml           # Main configuration
├── story_bible/              # Story bible templates
│   ├── story_bible_master.md
│   ├── world_summary.md
│   ├── magic_tech_systems.md
│   ├── character_bios/
│   ├── timeline.md
│   └── visual_references/
├── prompts/                  # LLM prompt templates
│   ├── prose_generation_prompt.txt
│   ├── refinement_pass1_cohesion.txt
│   ├── refinement_pass2_style.txt
│   ├── refinement_pass3_polish.txt
│   ├── style_guide.md
│   ├── act_outline_template.md
│   ├── chapter_outline_template.md
│   └── scene_outline_template.md
├── scripts/                  # Core Python scripts
│   ├── utils.py
│   ├── llm_client.py
│   ├── memory_manager.py
│   ├── generate_scene.py
│   ├── refine_scene.py
│   ├── assemble_chapter.py
│   └── export.py
├── outlines/                 # Story outlines
│   └── {BookName}/
│       ├── act_structure.md
│       ├── chapters/
│       └── scenes/
├── output/                   # Generated content
│   └── {BookName}/
│       ├── scenes/
│       │   ├── raw/
│       │   ├── refined/
│       │   └── final/
│       ├── chapters/
│       ├── images/
│       └── exports/
├── memory/                   # Vector database
│   ├── chroma_db/
│   └── embeddings/
├── storyapp.py              # Main CLI
├── requirements.txt
└── README.md
```

## Tips & Best Practices

### Writing Process

1. **Always outline first**: Never generate prose without a detailed scene outline
2. **Lock your outlines**: Finalize all outlines before generating prose
3. **Review regularly**: Check every 3-5 scenes to catch drift early
4. **Use memory system**: Initialize memory before starting generation
5. **Version control**: Use Git to track changes

### Prompt Engineering

- **Be specific**: Detailed scene outlines produce better results
- **Use examples**: Add example passages to style guide
- **Iterate**: Refine prompts based on output quality
- **Control**: Lock plot events in outline, let LLM handle prose

### Model Selection

- **8-12B models**: Best for laptop Arc GPU (Gemma-2, Llama-3, Mistral Nemo)
- **14B models**: Acceptable for reasoning tasks (DeepSeek-R1)
- **70B models**: Reserve for desktop server, final passes

### Workflow Efficiency

- Generate all scenes for a chapter before refining
- Run refinement in batch mode
- Use chapter assembly to catch issues
- Export regularly to review formatting

## Future Enhancements

- [ ] Image generation integration (Stable Diffusion)
- [ ] Audiobook TTS pipeline (Piper/Kokoro)
- [ ] Web UI for easier management
- [ ] Automated outline generation from story bible
- [ ] Character consistency checker
- [ ] Plot hole detector
- [ ] Multi-POV timeline manager

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Credits

- Inspired by the local LLM community
- Built with Ollama, ChromaDB, and Pandoc
- Optimized for Intel Arc GPUs

## Support

For issues and questions:

1. Check this README
2. Review the troubleshooting section
3. Open an issue on GitHub
4. Consult Ollama documentation: https://ollama.com/docs

---

**Happy Writing!**

Generated with StoryApp - Your AI-powered novel writing companion.
