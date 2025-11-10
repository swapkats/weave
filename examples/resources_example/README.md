# Resources Example

This example demonstrates how to use the Weave resources system to organize and reuse prompts, skills, and knowledge bases.

## Directory Structure

```
.weave/
├── prompts/          # System prompts for agents
│   └── content_writer.md
├── skills/           # Reusable skills
│   └── seo_optimization.yaml
├── knowledge/        # Knowledge bases
│   └── brand_voice.md
├── rules/            # Business rules
├── behaviors/        # Agent behaviors
└── memory/          # Agent memory storage
```

## Resource Types

### System Prompts (`@prompts/`)
Define agent instructions and personality. Can include:
- Markdown files with frontmatter for metadata
- Variable substitution with `{{variable}}`
- Tags and descriptions

### Skills (`@skills/`)
Reusable capability definitions that include:
- Step-by-step instructions
- Examples of usage
- Required tools
- Tags for categorization

### Knowledge Bases (`@knowledge/`)
Reference information for agents:
- Company information
- Brand guidelines
- Product documentation
- Domain knowledge

## Usage in Config

Reference resources using the `@type/name` syntax:

```yaml
agents:
  writer:
    model: "gpt-4"
    prompt: "@prompts/content_writer"         # Load system prompt
    skills: ["@skills/seo_optimization"]      # Load skills
    knowledge: ["@knowledge/brand_voice"]     # Load knowledge base
```

## Running the Example

```bash
# From the examples/resources_example directory
weave run content_pipeline

# Or with dry-run to see the flow
weave run content_pipeline --dry-run
```

## Benefits

1. **Reusability**: Define prompts and skills once, use across multiple agents
2. **Maintainability**: Update prompts in one place
3. **Organization**: Keep configuration clean and focused
4. **Version Control**: Track changes to prompts and knowledge bases
5. **Collaboration**: Share resources across team members
