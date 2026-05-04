package factories

import (
	"context"
	"fmt"
	"os"
	"strings"

	"adk-benchmark/src/application/tools"
	"adk-benchmark/src/domain"

	adkopenai "github.com/huytd/adk-openai-go"

	"google.golang.org/adk/agent"
	"google.golang.org/adk/agent/llmagent"
	"google.golang.org/adk/model"
	"google.golang.org/adk/tool"
	"google.golang.org/adk/tool/functiontool"
)

func initModel(ctx context.Context, modelName string) (model.LLM, error) {
	if strings.HasPrefix(modelName, "ollama_chat/") {
		actualName := strings.TrimPrefix(modelName, "ollama_chat/")
		if strings.HasSuffix(actualName, ":cloud") {
			actualName = strings.TrimSuffix(actualName, ":cloud")

			fmt.Printf("  [FACTORY] Podłączanie chmurowego modelu Ollama: %s\n", actualName)

			apiKey := os.Getenv("OLLAMA_API_KEY")
			if apiKey == "" {
				return nil, fmt.Errorf("missing OLLAMA_API_KEY")
			}

			cfg := &adkopenai.Config{
				BaseURL: "https://ollama.com/v1",
				APIKey:  apiKey,
			}

			return adkopenai.NewModel(actualName, cfg), nil
		}

		fmt.Printf("  [FACTORY] Podłączanie lokalnego modelu Ollama: %s\n", actualName)

		cfg := &adkopenai.Config{
			BaseURL: "http://localhost:11434/v1",
			APIKey:  "ollama",
		}

		return adkopenai.NewModel(actualName, cfg), nil
	}

	return nil, fmt.Errorf("unsupported model: %s", modelName)
}

func BuildAgent(ctx context.Context, modelName string) (agent.Agent, error) {
	validateNipTool, _ := functiontool.New(
		functiontool.Config{Name: "validate_nip", Description: "Sprawdza poprawność numeru NIP"},
		func(ctx tool.Context, input struct{ Nip string `json:"nip"` }) (tools.ValidationResult, error) {
			return tools.ValidateNip(input.Nip), nil
		},
	)

	calculateLineTool, _ := functiontool.New(
		functiontool.Config{Name: "calculate_line", Description: "Oblicza kwoty pozycji"},
		func(ctx tool.Context, input struct {
			Qty   float64 `json:"quantity"`
			Price float64 `json:"unit_price_net"`
			Vat   string  `json:"vat_rate"`
		}) (tools.LineCalculation, error) {
			return tools.CalculateLine(input.Qty, input.Price, input.Vat), nil
		},
	)

	calculateTotalsTool, _ := functiontool.New(
		functiontool.Config{Name: "calculate_totals", Description: "Oblicza sumy faktury"},
		func(ctx tool.Context, input struct {
			Lines []map[string]any `json:"lines"`
		}) (tools.TotalsCalculation, error) {
			return tools.CalculateTotals(input.Lines), nil
		},
	)

	formatInvoiceTool, _ := functiontool.New(
		functiontool.Config{Name: "format_invoice", Description: "Formatuje gotowy JSON faktury"},
		func(ctx tool.Context, input struct {
			Data map[string]any `json:"data"`
		}) (map[string]any, error) {
			return tools.FormatInvoice(input.Data), nil
		},
	)

	selectedModel, err := initModel(ctx, modelName)
	if err != nil {
		return nil, err
	}

	return llmagent.New(llmagent.Config{
		Name:        "invoice_agent",
		Model:       selectedModel,
		Instruction: domain.InvoiceAgentSystemPrompt,
		Tools:[]tool.Tool{validateNipTool, calculateLineTool, calculateTotalsTool, formatInvoiceTool},
	})
}