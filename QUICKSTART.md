# Quick Start Guide

Get up and running with StoryApp in 15 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python --version

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check if Pandoc is installed
pandoc --version
```

## Installation (5 minutes)

```bash
# 1. Navigate to project
cd "C:\Users\chamb\AI-ML Projects\StoryApp"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull required models (this takes a few minutes)
ollama pull gemma2:9b
ollama pull phi4:latest

# 4. Verify
python storyapp.py check-models
```

## Your First Scene (10 minutes)

### Step 1: Initialize Project (30 seconds)

```bash
python storyapp.py init "TestNovel"
```

### Step 2: Create Simple Story Bible (2 minutes)

Edit `story_bible/story_bible_master.md`:

```markdown
# Story Bible: TestNovel

## Elevator Pitch
A young detective solves her first murder case in a cyberpunk city.

## Three-Act Summary

### Act 1: Setup
Detective Maya receives her first solo case: a murdered tech executive.
She's eager to prove herself but quickly realizes nothing is as it seems.

### Act 2: Confrontation
Maya uncovers corporate espionage and a conspiracy that threatens
the entire city. She must decide whether to follow orders or seek truth.

### Act 3: Resolution
Maya exposes the conspiracy, but at great personal cost. She becomes
a true detective but loses her innocence.

## Core Themes
1. Truth vs. Loyalty
2. Growing up
3. Corporate power

## Protagonist: Maya Chen
- Age: 24
- Role: Junior Detective
- Want: Recognition and respect
- Need: To stand up for truth
- Arc: Naive → Disillusioned → Determined

## World
Near-future cyberpunk city (2045)
Technology: Advanced AI, neural implants
Society: Corporate-controlled, wealth gap extreme
```

### Step 3: Create Scene Outline (3 minutes)

Create `outlines/TestNovel/scenes/ch01_sc01.md`:

```markdown
# Scene Outline: Chapter 1, Scene 1

## Scene Metadata

**Scene Title**: The Call
**POV Character**: Maya Chen
**Timeline**: Day 1, Morning
**Primary Location**: Maya's apartment
**Estimated Word Count**: 1500

## Scene Purpose

**Plot Purpose**: Introduce Maya and present the inciting incident
**Character Purpose**: Show Maya's eagerness and inexperience
**Thematic Purpose**: Establish theme of ambition vs. reality

## Scene Structure

### BEGINNING: Setup

Maya wakes up in her small apartment. She's been a detective for 3 months
but hasn't gotten a real case yet. She goes through her morning routine,
checking her comm-link obsessively for assignments.

### MIDDLE: Conflict

The call finally comes: a murder case at Corp Tower. Maya is thrilled
but nervous. Her superior, Detective Reeves, warns her this is a test.
She has 48 hours to prove herself.

### END: Resolution/Transition

Maya arrives at the crime scene. The victim is high-profile. The scene
is already crawling with corporate security. Maya realizes this is way
bigger than she expected.

## Emotional Arc

**Enters Feeling**: Hopeful, eager
**Experiences**: Excitement → Nervousness → Determination
**Exits Feeling**: Out of her depth but committed

## Key Dialogue

1. **Reeves (phone)**: "Chen, you wanted a real case. Well, you got one."
2. **Maya**: "I won't let you down, sir."
3. **Reeves**: "We'll see. 48 hours, Detective."

## Sensory Details

**Sight**: Small, cluttered apartment; neon lights through window;
          sleek crime scene with holographic barriers
**Sound**: City hum, comm-link chime, nervous heartbeat
**Smell**: Synthetic coffee, sterile crime scene
**Touch**: Cold comm-link, smooth corp tower surfaces

## Reveals

- Maya is new and untested
- The victim is Alexander Kaine, tech executive
- Maya has 48 hours deadline
```

### Step 4: Initialize Memory (30 seconds)

```bash
python storyapp.py memory-init "TestNovel"
```

### Step 5: Generate Scene (2 minutes)

```bash
python storyapp.py generate "TestNovel" 1 1 "outlines/TestNovel/scenes/ch01_sc01.md"
```

This will create: `output/TestNovel/scenes/raw/chapter_01_scene_01_v1.md`

### Step 6: Review and Refine (3 minutes)

```bash
# View the generated scene
cat output/TestNovel/scenes/raw/chapter_01_scene_01_v1.md

# If satisfied, refine it
python storyapp.py refine "TestNovel" 1 1 -i "output/TestNovel/scenes/raw/chapter_01_scene_01_v1.md"
```

This creates the final polished version!

## Next Steps

### Create More Scenes

1. Create outlines for scenes 2 and 3
2. Generate them with the same process
3. Build out your chapter

### Assemble Chapter

```bash
python storyapp.py assemble "TestNovel" 1
```

### Export

```bash
python storyapp.py export "TestNovel" --title "Test Novel" --author "Your Name"
```

## Tips

- **Start small**: Write one chapter first to test the workflow
- **Iterate prompts**: Adjust `prompts/style_guide.md` based on output
- **Use examples**: Add sample prose you like to the style guide
- **Check memory**: Use `python storyapp.py status` to monitor system

## Troubleshooting

**Scene is too short/long?**
- Adjust `target_words`, `min_words`, `max_words` in `config/config.yaml`

**Prose style doesn't match expectations?**
- Edit `prompts/style_guide.md` with examples of your preferred style

**Generation is slow?**
- Use a smaller model: `llama3:8b` instead of `gemma2:9b`
- Reduce `num_ctx` in config

**Memory/continuity issues?**
- Re-run: `python storyapp.py memory-init "TestNovel"`

## Success!

You've now:
- ✓ Generated your first AI-assisted scene
- ✓ Refined it to publication quality
- ✓ Learned the basic workflow

You're ready to write your novel with StoryApp!

## Full Workflow Reminder

```
1. Story Bible → 2. Outlines → 3. Generate → 4. Refine → 5. Assemble → 6. Export
```

For the complete workflow, see [README.md](README.md)
