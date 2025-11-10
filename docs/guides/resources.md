# Resources

Load system prompts, skills, recipes, knowledge bases, rules, and agent behaviors from files and folders.

## Overview

The resources system allows you to organize agent configurations, prompts, and knowledge in a file-based structure. This makes it easy to:

- Version control your agent configurations
- Share prompts and skills across projects
- Organize knowledge bases and documentation
- Manage behavioral rules and constraints
- Define reusable workflow recipes

## Resource Types

Weave supports 7 types of resources:

| Type | Description | File Location |
|------|-------------|---------------|
| **System Prompts** | Agent system prompts and instructions | `.weave/prompts/` |
| **Skills** | Specific capabilities agents can perform | `.weave/skills/` |
| **Recipes** | Reusable workflow templates | `.weave/recipes/` |
| **Knowledge Bases** | Reference documentation and data | `.weave/knowledge/` |
| **Rules** | Behavioral rules and constraints | `.weave/rules/` |
| **Behaviors** | Agent personality and guidelines | `.weave/behaviors/` |
| **Sub-Agents** | Sub-agent prompt configurations | `.weave/sub_agents/` |

---

## Getting Started

### Initialize Resource Structure

Create the default directory structure with example files:

```bash
weave resources --create
```

**Output:**
```
✨ Created resource structure in .weave

Created directories:
  • prompts/     - System prompts
  • skills/      - Agent skills
  • recipes/     - Workflow recipes
  • knowledge/   - Knowledge bases
  • rules/       - Behavioral rules
  • behaviors/   - Agent behaviors
  • sub_agents/  - Sub-agent configurations

Example files have been created in each directory.
```

### List Resources

View all available resources:

```bash
# List all resources
weave resources

# Filter by type
weave resources --type skill
weave resources --type system_prompt

# Custom location
weave resources --path ./my-resources
```

**Output:**
```
Available Resources
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type           ┃ Count ┃ Names                ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ system_prompt  │ 1     │ helpful_assistant    │
│ skill          │ 1     │ data_analysis        │
│ recipe         │ 1     │ content_creation     │
│ knowledge_base │ 1     │ company_info         │
│ rule           │ 1     │ content_length_check │
│ behavior       │ 1     │ professional         │
│ sub_agent      │ 1     │ researcher           │
└────────────────┴───────┴──────────────────────┘

Total resources: 7
```

---

## Resource Types in Detail

### 1. System Prompts

System prompts define how agents should behave and respond.

**Location:** `.weave/prompts/`

**Format:** Markdown with YAML frontmatter

**Example:** `.weave/prompts/helpful_assistant.md`
```markdown
---
name: helpful_assistant
description: A helpful AI assistant system prompt
tags: [assistant, helpful]
variables:
  agent_name: "AI Assistant"
  role: "helpful assistant"
---

You are {{agent_name}}, a {{role}}.

Your goal is to:
- Help users accomplish their tasks
- Provide clear, accurate information
- Be friendly and professional

Always follow these guidelines:
1. Be concise and clear
2. Ask clarifying questions when needed
3. Admit when you don't know something
```

**Using in Config:**
```yaml
agents:
  my_agent:
    model: "gpt-4"
    prompt: "@prompts/helpful_assistant"  # Reference by path
```

---

### 2. Skills

Skills define specific capabilities that agents can perform.

**Location:** `.weave/skills/`

**Format:** YAML

**Example:** `.weave/skills/data_analysis.yaml`
```yaml
name: data_analysis
description: Analyze data and extract insights
instructions: |
  1. Review the provided data
  2. Identify patterns and trends
  3. Extract key insights
  4. Present findings clearly
examples:
  - "Analyze sales data for Q4 2023"
  - "Find trends in customer behavior"
required_tools:
  - data_cleaner
  - json_parser
tags:
  - data
  - analysis
```

**Using in Config:**
```yaml
agents:
  analyst:
    model: "gpt-4"
    skills: ["@skills/data_analysis"]
```

---

### 3. Recipes

Recipes define reusable workflow templates.

**Location:** `.weave/recipes/`

**Format:** YAML

**Example:** `.weave/recipes/content_creation.yaml`
```yaml
name: content_creation
description: Complete content creation workflow
steps:
  - step: research
    action: gather_information
    tools: [web_search]
  - step: outline
    action: create_outline
    input: research
  - step: draft
    action: write_content
    input: outline
  - step: edit
    action: refine_content
    input: draft
inputs:
  topic: string
  target_audience: string
outputs:
  final_content: string
tags:
  - content
  - writing
```

**Using Recipes:**
```python
from weave.resources import ResourceLoader

loader = ResourceLoader()
recipe = loader.get_resource(ResourceType.RECIPE, "content_creation")

# Execute recipe steps
for step in recipe.steps:
    print(f"Step: {step['step']}")
    print(f"Action: {step['action']}")
```

---

### 4. Knowledge Bases

Knowledge bases contain reference information and documentation.

**Location:** `.weave/knowledge/`

**Format:** Markdown, Text, or JSON

**Example:** `.weave/knowledge/company_info.md`
```markdown
# Company Information

## About Us
We are a technology company focused on AI solutions.

## Products
- Product A: AI-powered analytics
- Product B: Automation tools

## Values
- Innovation
- Quality
- Customer Focus
```

**Using in Config:**
```yaml
agents:
  support_agent:
    model: "gpt-4"
    knowledge: ["@knowledge/company_info"]
```

---

### 5. Rules

Rules define conditional behaviors and constraints.

**Location:** `.weave/rules/`

**Format:** YAML

**Example:** `.weave/rules/content_guidelines.yaml`
```yaml
name: content_length_check
condition: content_length > 5000
action: split_into_sections
priority: 10
enabled: true
description: Split long content into manageable sections
tags:
  - content
  - formatting
```

**Rule Properties:**
- `condition`: When the rule applies
- `action`: What to do
- `priority`: Execution order (higher = first)
- `enabled`: Whether rule is active

---

### 6. Behaviors

Behaviors define agent personality and communication style.

**Location:** `.weave/behaviors/`

**Format:** YAML

**Example:** `.weave/behaviors/professional.yaml`
```yaml
name: professional
personality: Professional, courteous, and detail-oriented
constraints:
  - Always use proper grammar
  - Avoid slang or casual language
  - Maintain professional tone
guidelines:
  - Be concise and clear
  - Use bullet points for lists
  - Cite sources when appropriate
examples:
  - input: "yo what's up"
    output: "Hello! How may I assist you today?"
  - input: "gimme the data"
    output: "Certainly, I'll provide the data analysis for you."
tags:
  - professional
  - business
```

**Using in Config:**
```yaml
agents:
  customer_service:
    model: "gpt-4"
    behavior: "@behaviors/professional"
```

---

### 7. Sub-Agents

Sub-agent configurations for specialized assistants.

**Location:** `.weave/sub_agents/`

**Format:** YAML

**Example:** `.weave/sub_agents/researcher.yaml`
```yaml
name: researcher
role: Research Specialist
instructions: |
  You are a research specialist focused on gathering accurate information.

  Your responsibilities:
  - Search for relevant sources
  - Verify information accuracy
  - Summarize key findings
  - Cite sources appropriately

  Always be thorough and factual.
context: Research assistant for the main agent
tools:
  - web_search
  - summarizer
tags:
  - research
  - information
```

---

## Loading Resources Programmatically

### Python API

```python
from weave.resources import ResourceLoader, ResourceType

# Create loader
loader = ResourceLoader(base_path=".weave")

# Load all resources
loader.load_all()

# Get specific resource
prompt = loader.get_resource(ResourceType.SYSTEM_PROMPT, "helpful_assistant")
skill = loader.get_resource(ResourceType.SKILL, "data_analysis")

# List resources
all_resources = loader.list_resources()
skills_only = loader.list_resources(ResourceType.SKILL)

# Use in your code
print(prompt.content)
print(f"Skill: {skill.name} - {skill.description}")
```

### Variable Substitution

System prompts support variable substitution:

```python
from weave.resources import ResourceLoader

loader = ResourceLoader()
loader.load_all()

prompt = loader.get_resource(ResourceType.SYSTEM_PROMPT, "helpful_assistant")

# Substitute variables
content = prompt.content
for var, value in prompt.variables.items():
    content = content.replace(f"{{{{{var}}}}}", value)

print(content)
```

---

## File Organization

### Recommended Structure

```
project/
├── .weave/
│   ├── prompts/
│   │   ├── system.md
│   │   ├── assistant.md
│   │   └── specialist.md
│   ├── skills/
│   │   ├── analysis.yaml
│   │   ├── research.yaml
│   │   └── writing.yaml
│   ├── recipes/
│   │   ├── content_workflow.yaml
│   │   └── data_pipeline.yaml
│   ├── knowledge/
│   │   ├── company.md
│   │   ├── products.md
│   │   └── faq.json
│   ├── rules/
│   │   ├── formatting.yaml
│   │   └── validation.yaml
│   ├── behaviors/
│   │   ├── professional.yaml
│   │   └── friendly.yaml
│   └── sub_agents/
│       ├── researcher.yaml
│       └── editor.yaml
├── .weave.yaml
└── README.md
```

### Naming Conventions

- Use lowercase with underscores: `data_analysis.yaml`
- Be descriptive: `professional_customer_service.yaml` not `style1.yaml`
- Group related files: `analysis_*.yaml`, `research_*.md`

---

## Integration with Agents

### Reference Resources in Config

```yaml
agents:
  content_creator:
    model: "gpt-4"
    prompt: "@prompts/creative_writer"
    skills:
      - "@skills/content_creation"
      - "@skills/seo_optimization"
    behavior: "@behaviors/creative"
    knowledge:
      - "@knowledge/brand_guidelines"
      - "@knowledge/style_guide"
    tools:
      - web_search
      - markdown_formatter
```

### Loading at Runtime

Resources are loaded automatically when agents are initialized:

```python
from weave.parser import load_config_from_path
from weave.resources import ResourceLoader

# Load config
config = load_config_from_path(".weave.yaml")

# Load resources
loader = ResourceLoader()
loader.load_all()

# Resources are available to agents
```

---

## Best Practices

### 1. Version Control

```bash
# Add .weave/ to git
git add .weave/
git commit -m "Add agent resources"
```

### 2. Environment-Specific Resources

```
.weave/
├── prompts/
│   ├── common/
│   │   └── base.md
│   ├── dev/
│   │   └── debug.md
│   └── prod/
│       └── production.md
```

### 3. Modular Organization

Break large prompts into smaller, reusable pieces:

```
prompts/
├── base_instructions.md
├── personality_traits.md
└── domain_expertise.md
```

### 4. Documentation

Add descriptions and tags to all resources:

```yaml
name: my_skill
description: Clear description of what this skill does
tags: [category, use-case, domain]
```

### 5. Testing

Test resources independently:

```python
# test_resources.py
from weave.resources import ResourceLoader

def test_prompt_loads():
    loader = ResourceLoader()
    prompt = loader.get_resource(ResourceType.SYSTEM_PROMPT, "my_prompt")
    assert prompt is not None
    assert "{{agent_name}}" in prompt.content
```

---

## Common Patterns

### Pattern 1: Role-Based Prompts

```
prompts/
├── roles/
│   ├── analyst.md
│   ├── writer.md
│   └── reviewer.md
```

### Pattern 2: Domain-Specific Knowledge

```
knowledge/
├── finance/
│   ├── regulations.md
│   └── terminology.md
├── healthcare/
│   └── hipaa_guidelines.md
└── tech/
    └── api_docs.json
```

### Pattern 3: Workflow Recipes

```
recipes/
├── content/
│   ├── blog_post.yaml
│   └── social_media.yaml
└── data/
    ├── etl_pipeline.yaml
    └── analysis_workflow.yaml
```

---

## Troubleshooting

### Resources Not Found

```bash
# Verify directory exists
ls -la .weave/

# Create if missing
weave resources --create

# Check resources loaded
weave resources
```

### YAML Parsing Errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.weave/skills/my_skill.yaml'))"
```

### Variable Substitution Not Working

Ensure variables are defined in frontmatter:

```markdown
---
variables:
  my_var: "value"
---

Use {{my_var}} in content
```

---

## Examples

### Example 1: Customer Support Agent

**.weave/prompts/support_agent.md:**
```markdown
---
name: customer_support
variables:
  company_name: "Acme Corp"
  support_hours: "9 AM - 5 PM EST"
---

You are a customer support agent for {{company_name}}.

Support hours: {{support_hours}}

Always be helpful, patient, and professional.
```

**.weave/knowledge/support_kb.md:**
```markdown
# Support Knowledge Base

## Common Issues
- Password reset: Guide users to reset page
- Billing questions: Transfer to billing team
- Technical issues: Collect error details
```

**.weave.yaml:**
```yaml
agents:
  support:
    model: "gpt-4"
    prompt: "@prompts/support_agent"
    knowledge: ["@knowledge/support_kb"]
    behavior: "@behaviors/professional"
```

---

## Future Enhancements (v2.0)

- **Remote Resources** - Load from URLs or cloud storage
- **Resource Templates** - Generate resources from templates
- **Hot Reloading** - Auto-reload when files change
- **Resource Validation** - Validate resource schemas
- **Resource Registry** - Share resources across projects

---

## Next Steps

- [Writing Configurations](writing-configs.md) - Using resources in configs
- [Plugins](plugins.md) - Extending with plugins
- [CLI Commands](../reference/cli-commands.md) - Command reference
