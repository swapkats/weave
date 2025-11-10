# Resources Example

This example demonstrates Weave's resource management system for organizing agent prompts, skills, and knowledge bases.

## Structure

```
resources_example/
├── .weave/                    # Resources directory
│   ├── prompts/               # System prompts
│   │   └── content_writer.md
│   ├── skills/                # Agent skills
│   │   └── seo_optimization.yaml
│   └── knowledge/             # Knowledge bases
│       └── brand_voice.md
├── .weave.yaml                # Main configuration
└── README.md
```

## Features Demonstrated

1. **System Prompts** - Markdown files with YAML frontmatter
2. **Skills** - YAML definitions of agent capabilities
3. **Knowledge Bases** - Reference documentation for agents

## Usage

### Initialize Resources

```bash
# Create default structure
weave resources --create

# List available resources
weave resources

# Filter by type
weave resources --type skill
```

### Run the Pipeline

```bash
# Preview execution plan
weave plan

# Execute the workflow
weave apply
```

## Resource Files

### System Prompt
`.weave/prompts/content_writer.md` - Professional content writing instructions with:
- Role definition
- Writing guidelines
- Quality standards
- Variable substitution support

### Skill
`.weave/skills/seo_optimization.yaml` - SEO optimization capability with:
- Step-by-step instructions
- Examples
- Required tools
- Tags for organization

### Knowledge Base
`.weave/knowledge/brand_voice.md` - Brand voice guidelines including:
- Personality traits
- Writing style rules
- Examples of good/bad content
- Approved/avoided terminology

## Loading Resources Programmatically

```python
from weave.resources import ResourceLoader, ResourceType

# Create loader
loader = ResourceLoader(base_path=".weave")

# Load all resources
loader.load_all()

# Access specific resources
prompt = loader.get_resource(ResourceType.SYSTEM_PROMPT, "content_writer")
skill = loader.get_resource(ResourceType.SKILL, "seo_optimization")
kb = loader.get_resource(ResourceType.KNOWLEDGE_BASE, "brand_voice")

# Use in your agents
print(f"Prompt: {prompt.name}")
print(f"Content: {prompt.content}")
print(f"Variables: {prompt.variables}")

print(f"\nSkill: {skill.name}")
print(f"Instructions: {skill.instructions}")

print(f"\nKnowledge: {kb.name}")
print(f"Format: {kb.format}")
```

## Benefits

1. **Version Control** - Track changes to prompts and configurations
2. **Reusability** - Share resources across projects
3. **Organization** - Structured file system for agent resources
4. **Collaboration** - Easy for teams to contribute and update
5. **Testing** - Test prompts and skills independently

## Next Steps

- Add more prompts for different writing styles
- Create additional skills for various tasks
- Expand knowledge bases with domain expertise
- Implement behaviors and rules for agent constraints
- Define sub-agents for specialized tasks
