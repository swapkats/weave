# Coding Agent Example

AI-powered software development workflow demonstrating agent composition for complete coding tasks.

## Overview

This example shows how to build a complete coding workflow using multiple specialized AI agents that work together to analyze requirements, generate code, create tests, review quality, and produce documentation.

## Workflow Stages

```
Requirements → Code Generation → Testing → Review → Documentation → Refactoring
```

## Agents

### 1. Requirements Analyzer
- Breaks down requirements into implementable tasks
- Creates technical specifications
- Identifies dependencies and risks
- **Output**: Structured requirements specification

### 2. Code Generator
- Generates clean, production-ready code
- Follows language best practices
- Includes comprehensive documentation
- **Output**: Implementation code

### 3. Test Generator
- Creates unit and integration tests
- Aims for 80%+ coverage
- Tests happy paths and edge cases
- **Output**: Comprehensive test suite

### 4. Code Reviewer
- Reviews code quality and security
- Identifies issues by severity
- Provides actionable feedback
- **Output**: Detailed review report

### 5. Documentation Writer
- Creates README and API docs
- Writes user and developer guides
- Includes examples and troubleshooting
- **Output**: Complete documentation

### 6. Refactoring Agent
- Improves code based on review feedback
- Maintains functionality while enhancing quality
- Documents all changes made
- **Output**: Refactored, improved code

## Workflows

### Full Coding Workflow
Complete end-to-end development from requirements to production code.

```bash
weave plan     # Preview the workflow
weave apply    # Execute full workflow
```

**Use for**: New features, complete module implementation

### Quick Prototype
Fast iteration for proof-of-concepts (requirements → code → tests).

```bash
weave apply quick_prototype
```

**Use for**: POCs, prototypes, experiments

### Code Review Only
Review existing code without generation.

```bash
weave apply code_review_only
```

**Use for**: PR reviews, code audits

### TDD Workflow
Test-driven development approach (requirements → tests → code → review).

```bash
weave apply tdd_workflow
```

**Use for**: Critical functionality, high-quality code

## Resource Files

### Prompts (`.weave/prompts/`)
- `requirements_analyzer.md` - Requirements analysis system prompt
- `code_generator.md` - Code generation guidelines

### Skills (`.weave/skills/`)
- `clean_code.yaml` - Clean code principles
- `test_automation.yaml` - Test automation best practices
- `refactoring.yaml` - Refactoring techniques

### Knowledge (`.weave/knowledge/`)
- `code_review_checklist.md` - Comprehensive review checklist
- `documentation_guide.md` - Documentation standards

## Configuration

The `.weave.yaml` file defines:
- **Environment variables**: Default model, language, test framework
- **Custom tools**: file_writer, test_runner, code_analyzer
- **Agent definitions**: Models, prompts, tools, dependencies
- **Workflows**: Different execution modes
- **Runtime settings**: Timeouts, retries, resource limits

## Usage Examples

### Generate a New Feature

```bash
# Initialize the workflow
weave plan

# Execute with custom inputs
weave apply --input "Create a user authentication system with JWT"
```

### Review Existing Code

```bash
weave apply code_review_only --input "Review src/auth.py"
```

### Run Tests on Generated Code

```bash
# After code generation
weave apply test_focused
```

## Customization

### Change Programming Language

Edit `.weave.yaml`:
```yaml
env:
  CODE_LANGUAGE: "javascript"  # or "java", "go", etc.
  TEST_FRAMEWORK: "jest"
```

### Adjust Agent Behavior

Modify system prompts in `.weave/prompts/` to change agent behavior.

### Add Custom Tools

Define new tools in the `tools:` section of `.weave.yaml`.

## Storage

Generated artifacts are stored in:
```
.weave/storage/
├── code_outputs/     # Generated code files
├── test_results/     # Test execution results
└── review_reports/   # Code review reports
```

Retention: 30 days (configurable in storage.retention)

## Observability

Logs are written to:
```
.weave/logs/coding-workflow.log
```

Enable metrics and tracing in the `observability:` section.

## Best Practices

1. **Start Small**: Begin with quick_prototype for new ideas
2. **Iterate**: Use feedback from code_reviewer to improve
3. **Review Specs**: Ensure requirements are clear before generation
4. **Test First**: Consider tdd_workflow for critical code
5. **Document**: Always run full workflow for production code

## Requirements

- Python 3.8+ (for weave CLI)
- OpenAI API key or compatible LLM provider
- Development tools for target language (Python, Node.js, etc.)

## Troubleshooting

### Agent Timeout
Increase timeout in workflow definition:
```yaml
runtime:
  timeout: 7200  # 2 hours
```

### Out of Memory
Reduce max_workers or increase memory limit:
```yaml
runtime:
  executor:
    max_workers: 2
  resource_limits:
    max_memory_mb: 8192
```

### Code Quality Issues
Adjust code_generator temperature for more deterministic output:
```yaml
agents:
  code_generator:
    config:
      temperature: 0.2  # More deterministic
```

## Next Steps

- Add more skills for specialized coding patterns
- Create language-specific knowledge bases
- Implement custom tools for your tech stack
- Add deployment workflows
- Integrate with CI/CD pipelines

## Learn More

- [Weave Documentation](../../docs/)
- [Configuration Reference](../../docs/reference/configuration.md)
- [Best Practices](../../docs/guides/best-practices.md)
