# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **multi-agent Liuyao (Six-Line Divination) interpretation system** that uses three specialized agents representing different divination schools (Traditional Orthodox, Xiangshu/Numerical, and Mangpai/Blind School) to analyze hexagrams through a 10-round debate process.

## Development Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys (minimum one required: KIMI_API_KEY, GLM_API_KEY, DEEPSEEK_API_KEY, etc.)
```

## Common Commands

### Testing LLM Clients
```bash
# Test all configured LLM providers
python tests/test_llm_clients.py

# Run specific provider tests (edit file to run specific function)
python tests/test_llm_clients.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage report
pytest --cov=liuyao_decoder --cov-report=html
```

### Running the Application
```bash
# Main entry point (not yet implemented - currently in Phase 2)
python main.py
```

## Architecture Overview

### Multi-Agent Debate System

The system uses three specialized agents that engage in structured debate:

1. **Traditional Agent** (`agents/traditional_agent.py`) - Follows orthodox methods from classical texts
2. **Xiangshu Agent** (`agents/xiangshu_agent.py`) - Focuses on numerical patterns and structural relationships
3. **Mangpai Agent** (`agents/mangpai_agent.py`) - Uses practical, heuristic-based approaches

Each agent inherits from `BaseAgent` (`agents/base_agent.py`) and implements:
- `interpret(hexagram)` - Initial hexagram interpretation
- `debate(hexagram, debate_history, round_number)` - Multi-round debate participation

### LLM Abstraction Layer

All LLM providers implement `BaseLLMClient` (`llm/base.py`):

**Supported Providers:**
- Kimi (Moonshot) - Default, optimized for China
- GLM (Zhipu) - Domestic alternative
- DeepSeek - Domestic alternative
- OpenAI GPT - International
- Anthropic Claude - International
- Google Gemini - International

**Factory Pattern:** Use `LLMClientFactory.create(provider_name, api_key, model)` to instantiate clients.

### Data Flow

1. **Input:** `HexagramInput` model contains hexagram data (lines, timing, transformations)
2. **Processing:** Each agent interprets independently → debate rounds (max 10)
3. **Convergence:** System detects when consensus is reached (configurable threshold)
4. **Output:** Comprehensive report with conclusions from all schools

### Configuration

All configuration is centralized in `config/config.yaml`:

- **LLM clients:** API keys, models, temperature, max_tokens
- **Agents:** Which LLM each agent uses, prompt file paths
- **Debate settings:** max_rounds (10), convergence_threshold (0.9), confidence_stability_threshold (0.5)
- **Storage:** SQLite/PostgreSQL configuration
- **Literature search:** Keyword-based or vector-based search

### Data Models (`storage/models.py`)

Core Pydantic models:
- `HexagramInput` - Structured hexagram data (lines, timing, question)
- `AgentResponse` - Agent outputs with confidence scores
- `DebateContext` - Debate state management across rounds
- `SchoolType` - Enum: TRADITIONAL, XIANGSHU, MANGPAI

### Prompts

Each school has dedicated prompt templates in `prompts/`:
- `traditional.md` - Traditional orthodox school guidance
- `xiangshu.md` - Numerical/structural school guidance
- `mangpai.md` - Blind school practical guidance

Prompts are loaded by agents during initialization and used to construct both initial interpretation prompts and debate round prompts.

## LLM Provider Selection

**For Chinese users (recommended order):**
1. Kimi - Best performance, no proxy needed
2. GLM - Good alternative, no proxy needed
3. DeepSeek - Good alternative, no proxy needed

**For international users:**
- OpenAI GPT-4, Anthropic Claude, Google Gemini (require proxy)

## Important Implementation Details

### Agent Prompt Construction

`BaseAgent._build_initial_prompt()` creates detailed prompts including:
- Question and hexagram info
- Six lines with shen, liuqin, wuxing, yin_yang attributes
- Structured output format requiring confidence scores

`BaseAgent._build_debate_prompt()` creates debate prompts including:
- Debate history summary from previous rounds
- Structured response format requiring:
  - Preserved viewpoints
  - Viewpoint adjustments with theoretical consistency
  - Responses to other agents
  - Optional literature search results
  - Confidence scores with adjustment reasoning

### Confidence Tracking

Each agent response includes a confidence score (0-10). The system:
- Extracts confidence from response content using regex patterns
- Validates scores are within bounds
- Tracks confidence changes across debate rounds

### Error Handling

Agents validate responses using `validate_response()`:
- Checks content is not empty
- Ensures confidence is in range [0, 10]
- Logs warnings for out-of-range values

## Current Development Status

**Phase 2 (In Progress):** Agent System Implementation
- ✅ LLM abstraction layer (all 6 providers)
- ✅ Data models with Pydantic
- ✅ Configuration loading
- 🔄 Agent base class and implementations
- 🔄 Hexagram input parser

**Planned Phases:**
- Phase 3: Debate management system, state machine, convergence detector
- Phase 4: Persistent storage (SQLite/PostgreSQL)
- Phase 5: Literature search functionality
- Phase 6: Report generation
- Phase 7: Performance optimization and testing

## Testing Strategy

The project uses pytest with the following structure:
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for multi-component workflows
- `tests/e2e/` - End-to-end tests for complete divination flows

Current main test: `tests/test_llm_clients.py` - Tests all LLM providers for basic connectivity and response handling.

## Key Design Patterns

1. **Abstract Base Classes** - `BaseAgent`, `BaseLLMClient` define interfaces
2. **Factory Pattern** - `LLMClientFactory` creates provider instances
3. **Composition** - Agents contain LLM clients, not inherit from them
4. **Data Validation** - Pydantic models throughout for type safety
5. **Configuration-Driven** - YAML config with environment variable substitution
