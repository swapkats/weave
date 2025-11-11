# Using Google Gemini with Weave

Google Gemini models now support OpenAI-compatible API, making it easy to use with Weave.

## Quick Setup

### 1. Get Your Google API Key

Visit https://aistudio.google.com/app/apikey to create an API key.

### 2. Configure `.agent/.env`

```bash
# Copy the example file
cp .agent/.env.example .agent/.env

# Edit it and add:
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_API_KEY=your-google-api-key-here
```

### 3. Create Your Agent Config

```yaml
# .agent.yaml
version: "1.0"

agents:
  gemini_agent:
    model: "gemini-2.0-flash-exp"
    # or: gemini-1.5-pro, gemini-1.5-flash
    prompt: "You are a helpful AI assistant"
    config:
      temperature: 0.7
      max_tokens: 2000
```

### 4. Run It!

```bash
source .venv/bin/activate
weave plan
weave apply
```

## Available Gemini Models

Google's OpenAI-compatible API supports these models:

- **gemini-2.0-flash-exp** - Latest experimental model, fastest
- **gemini-1.5-pro** - Most capable, best for complex tasks
- **gemini-1.5-flash** - Fast and efficient
- **gemini-1.5-flash-8b** - Smaller, faster variant

## Complete Example

```bash
# .agent/.env
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_API_KEY=AIzaSyD-your-actual-key-here
```

```yaml
# .agent.yaml
version: "1.0"

agents:
  researcher:
    model: "gemini-1.5-pro"
    tools:
      - web_search
      - file_read
    prompt: |
      You are a research assistant. Gather information from
      the web and provide detailed, well-sourced summaries.
    config:
      temperature: 0.7
      max_tokens: 4000

  writer:
    model: "gemini-2.0-flash-exp"
    inputs: "researcher"
    prompt: |
      You are a content writer. Take the research provided
      and create engaging, well-structured articles.
    config:
      temperature: 0.9
      max_tokens: 3000

weaves:
  content_pipeline:
    description: "Research and write articles using Gemini"
    agents:
      - researcher
      - writer
```

## How It Works

When you set `OPENAI_BASE_URL`, Weave automatically routes ALL models (except Claude) through the OpenAI client with your custom endpoint. This means:

1. **Gemini models**: Work perfectly with their native names
2. **Local models**: Use `OPENAI_BASE_URL=http://localhost:1234/v1`
3. **Other providers**: Any OpenAI-compatible API works

The model detection logic:
```python
# 1. Check if model is Claude → use Anthropic client
if "claude" in model:
    use_anthropic()

# 2. Check if custom endpoint → use OpenAI client (for Gemini, etc.)
elif OPENAI_BASE_URL is set:
    use_openai()  # Works with ANY model name!

# 3. Default OpenAI → use OpenAI client
elif "gpt" in model:
    use_openai()
```

## Switching Between Providers

You can easily switch between OpenAI and Gemini:

### For OpenAI (GPT):
```bash
# .agent/.env
OPENAI_API_KEY=sk-your-openai-key
# Don't set OPENAI_BASE_URL
```

```yaml
model: "gpt-4"
```

### For Gemini:
```bash
# .agent/.env
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_API_KEY=your-google-api-key
```

```yaml
model: "gemini-2.0-flash-exp"
```

### For Both in Same Config:
```bash
# .agent/.env
# Leave OPENAI_BASE_URL unset
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

```yaml
agents:
  gpt_agent:
    model: "gpt-4"

  claude_agent:
    model: "claude-3-opus"
```

Note: You can't use both Gemini and GPT in the same run because they both use the OpenAI client. To use Gemini, set `OPENAI_BASE_URL` which redirects ALL OpenAI calls to Gemini.

## Pricing

Gemini is significantly cheaper than GPT-4:

- **gemini-2.0-flash-exp**: Free during preview
- **gemini-1.5-pro**: $0.00125 / 1K input tokens
- **gemini-1.5-flash**: $0.000075 / 1K input tokens

Compare to GPT-4: $0.03 / 1K input tokens

## Troubleshooting

### "Unsupported model" error

Make sure you set `OPENAI_BASE_URL`:
```bash
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

### API key not working

1. Check you're using the correct key format (starts with `AIzaSy`)
2. Make sure the API key has Generative Language API enabled
3. Visit https://aistudio.google.com/app/apikey

### Rate limits

Google has generous free tier limits:
- 15 requests per minute
- 1 million tokens per minute
- 1500 requests per day

For production, enable billing for higher limits.

## Resources

- Google AI Studio: https://aistudio.google.com
- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- OpenAI Compatibility: https://ai.google.dev/gemini-api/docs/openai
