package infrastructure

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"strings"
	"sync"
	"time"

	"adk-benchmark/src/domain"
)

var csvMutex sync.Mutex

type MetricsService struct {
	Model            string
	Framework        string
	StartWall        time.Time
	TTFR             *float64
	EndWall          time.Time
	LLMRounds        int
	TokensInput      int
	TokensOutput     int
	RamSamples       []uint64
	ConversationLog[]map[string]any
	FinalInvoiceJSON map[string]any
	Quality          map[string]any
}

func NewMetricsService(model string) *MetricsService {
	return &MetricsService{
		Model:           model,
		Framework:       "adk-go",
		StartWall:       time.Now(),
		RamSamples:      make([]uint64, 0),
		ConversationLog: make([]map[string]any, 0),
	}
}

func (m *MetricsService) SampleRAM() {
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)
	m.RamSamples = append(m.RamSamples, mem.Alloc/1024/1024)
}

func (m *MetricsService) RecordFirstResponse() {
	if m.TTFR == nil {
		t := time.Since(m.StartWall).Seconds()
		m.TTFR = &t
	}
}

func (m *MetricsService) RecordLLMCall(tokensIn, tokensOut int) {
	m.LLMRounds++
	m.TokensInput += tokensIn
	m.TokensOutput += tokensOut
}

func (m *MetricsService) LogTurn(role, content string, meta map[string]any) {
	if len(content) > 2000 {
		content = content[:2000]
	}
	if meta == nil {
		meta = map[string]any{}
	}
	entry := map[string]any{
		"turn":          len(m.ConversationLog) + 1,
		"role":          role,
		"content":       content,
		"meta":          meta,
		"wall_offset_s": time.Since(m.StartWall).Seconds(),
	}
	m.ConversationLog = append(m.ConversationLog, entry)
}

func (m *MetricsService) Finish() {
	m.EndWall = time.Now()
	m.SampleRAM()
}

func (m *MetricsService) ToDict() map[string]any {
	maxRam := uint64(0)
	for _, r := range m.RamSamples {
		if r > maxRam {
			maxRam = r
		}
	}

	ttfr := 0.0
	if m.TTFR != nil {
		ttfr = *m.TTFR
	}

	return map[string]any{
		"timestamp":          time.Now().Format(time.RFC3339),
		"framework":          m.Framework,
		"model":              m.Model,
		"ttfr_s":             ttfr,
		"total_time_s":       m.EndWall.Sub(m.StartWall).Seconds(),
		"llm_rounds":         m.LLMRounds,
		"tokens_input":       m.TokensInput,
		"tokens_output":      m.TokensOutput,
		"tokens_total":       m.TokensInput + m.TokensOutput,
		"ram_peak_mb":        maxRam,
		"quality":            m.Quality,
		"final_invoice_json": m.FinalInvoiceJSON,
		"conversation_log":   m.ConversationLog,
	}
}

func (m *MetricsService) Save() string {
	data := m.ToDict()
	resultsDir := domain.GetResultsDir()
	os.MkdirAll(resultsDir, 0755)

	slug := strings.ReplaceAll(m.Model, "/", "-")
	filename := fmt.Sprintf("%s/%s_%s_%d.json", resultsDir, m.Framework, slug, time.Now().Unix())

	bytes, _ := json.MarshalIndent(data, "", "  ")
	os.WriteFile(filename, bytes, 0644)

	csvMutex.Lock()
	defer csvMutex.Unlock()

	csvPath := domain.GetSummaryCSVPath()
	header := "framework,model,ttfr_s,total_time_s,llm_rounds,tokens_input,tokens_output,tokens_total,ram_peak_mb,auto_score,invoice_json_ok,timestamp\n"

	if _, err := os.Stat(csvPath); os.IsNotExist(err) {
		os.WriteFile(csvPath,[]byte(header), 0644)
	}

	hasJSON := 0
	if m.FinalInvoiceJSON != nil {
		hasJSON = 1
	}

	row := fmt.Sprintf("%s,%s,%.3f,%.3f,%d,%d,%d,%d,%d,%.2f,%d,%s\n",
		data["framework"], data["model"], data["ttfr_s"], data["total_time_s"],
		data["llm_rounds"], data["tokens_input"], data["tokens_output"], data["tokens_total"],
		data["ram_peak_mb"], m.Quality["auto_score_0_5"], hasJSON, data["timestamp"])

	f, _ := os.OpenFile(csvPath, os.O_APPEND|os.O_WRONLY, 0644)
	defer f.Close()
	f.WriteString(row)

	return filename
}