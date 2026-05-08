# Invoice Agent Benchmark

Benchmark comparing agentic framework implementations for VAT invoice generation. The project tests quality, performance, and developer experience when building conversational agents.

## Project Goal

Comparison of agentic frameworks across:
- **Quality** - JSON completeness and correctness, schema validation
- **Performance** - time to first response (TTFR), total execution time, token count
- **Developer Experience** - implementation ease, documentation, debugging

## Implementations

The project contains the following invoice agent implementations:

| Implementation | Framework | Language | 
|---|---|---|
| [adk-python](./adk-python) | Google ADK | Python |
| [adk-typescript](./adk-typescript) | Google ADK | TypeScript |
| [adk-go](./adk-go) | Google ADK | Go |
| [baseline](./baseline) | None (Custom) | Python |
| [koog-kotlin](./koog-kotlin) | JetBrains Koog | Kotlin |

## Test Scenario

Each implementation handles the same scenario:
- Collecting seller and buyer information
- NIP (Polish tax ID) verification
- Gathering invoice line items (quantity, price, VAT)
- Calculating net, VAT, and gross totals
- Returning a complete invoice JSON

The agent conducts a natural conversation and asks for missing data.

## Quick Start

### Prerequisites
- Python 3.10+ (for adk-python and baseline)
- Node.js 18+ (for adk-typescript)
- Go 1.21+ (for adk-go)
- Kotlin/Gradle (for koog-kotlin)
- `uv` package manager (for Python projects)
- Local LLM model (Ollama) or API access

### Running Python ADK

```bash
cd adk-python
uv sync
uv run agent.py
```

### Running TypeScript

```bash
cd adk-typescript
npm install
npm start
```

### Running Go

```bash
cd adk-go
go run ./agent.go
```

### Running Baseline (Python)

```bash
cd baseline
uv sync
uv run agent.py
```

### Debug Mode

All implementations support debug mode:

```bash
uv run agent.py --debug      # Python
go run ./agent.go --debug    # Go
npm start -- --debug        # TypeScript
```

## Benchmark Results

Detailed results are available in [RAPORT.md](./RAPORT.md)

Key metrics:
- **TTFR** (Time To First Response) - time to first response
- **Total Time** - total agent execution time
- **LLM Rounds** - number of model interactions
- **Tokens** - total tokens consumed
- **JSON OK** - whether the returned JSON is complete
- **Schema OK** - whether JSON passed schema validation

### Summary Results

Comparison table of best configurations for each framework is available in [RAPORT.md](./RAPORT.md).

## Project Structure

```
invoice-agent-benchmark/
├── README.md                    # This file
├── RAPORT.md                    # Detailed benchmark report
├── adk-python/                  # Python + Google ADK implementation
│   ├── agent.py                 # Main agent
│   ├── src/
│   │   ├── application/         # Application logic
│   │   ├── domain/              # Business models and rules
│   │   ├── infrastructure/      # LLM integration
│   │   └── interfaces/          # Tools
│   └── pyproject.toml           # Dependencies
├── adk-typescript/              # TypeScript + Google ADK implementation
│   ├── agent.ts                 # Main agent
│   ├── src/                     # Structure like Python version
│   ├── package.json
│   └── tsconfig.json
├── adk-go/                      # Go + Google ADK implementation
│   ├── agent.go                 # Main agent
│   ├── src/                     # Structure like Python version
│   └── go.mod
├── baseline/                    # Reference implementation (no framework)
│   ├── agent.py
│   ├── src/                     # Structure like Python version
│   └── pyproject.toml
├── koog-kotlin/                 # Kotlin + Koog implementation
│   ├── Agent.kt
│   ├── build.gradle.kts
│   └── src/main/
└── results/                     # Benchmark results
    ├── summary.csv              # Aggregated results
    └── raw/                     # Individual run logs

```

## Tools

Each agent has access to the same tools:

1. **validate_nip** - validates Polish NIP tax ID format
2. **calculate_line** - calculates invoice line item value (gross price)
3. **calculate_totals** - sums net, VAT, and gross totals
4. **format_invoice** - formats and confirms final invoice

## Logged Metrics

Each agent run records:
- Time to first response (TTFR)
- Total execution time
- Number of LLM rounds
- Token count (input/output)
- RAM usage
- Quality score (0-5)
- Generated JSON correctness
- Schema validation result

## Further Resources

- [Google ADK Documentation](https://adk.dev/get-started/)
- [JetBrains Koog](https://www.jetbrains.com/koog/)
- [RAPORT.md](./RAPORT.md) - Detailed benchmark results
