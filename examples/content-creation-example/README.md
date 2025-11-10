# Content Creation Example

AI-powered content creation workflow for blog posts, articles, and marketing copy.

## Workflow

```
Research → Write → Edit → Publish
```

## Agents

1. **Researcher** - Gathers information and sources
2. **Writer** - Creates engaging content
3. **Editor** - Polishes and optimizes for SEO

## Usage

```bash
# Full workflow
weave apply

# Quick write (skip research)
weave apply quick_write

# Custom topic
weave apply --input "AI agents in healthcare"
```

## Customize

Edit `.weave.yaml` to change:
- Content type (blog-post, article, social-media)
- Word count target
- Tone and style
- SEO focus

## Output

Content is saved to `.weave/storage/` with:
- Research findings
- Draft content
- Final edited version with SEO metadata
