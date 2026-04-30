import os
import re
import time
import json
import psutil
from datetime import datetime
from pathlib import Path

from src.domain.config import RESULTS_DIR, SUMMARY_CSV_PATH

class MetricsService:
    def __init__(self, model: str, framework: str = "adk-python"):
        self.model = model
        self.framework = framework
        self.start_wall = time.perf_counter()
        self.ttfr: float | None = None
        self.end_wall: float | None = None
        self.llm_rounds = 0
        self.tokens_input = 0
        self.tokens_output = 0
        self.ram_samples: list[int] = []
        self.conversation_log: list[dict] =[]
        self._proc = psutil.Process(os.getpid())
        self.final_invoice_json: dict | None = None
        self.quality: dict = {}

    def sample_ram(self):
        if self._proc:
            try:
                self.ram_samples.append(self._proc.memory_info().rss // 1024 // 1024)
            except Exception:
                pass

    def record_first_response(self):
        if self.ttfr is None:
            self.ttfr = round(time.perf_counter() - self.start_wall, 3)

    def record_llm_call(self, tokens_in: int = 0, tokens_out: int = 0):
        self.llm_rounds += 1
        self.tokens_input += tokens_in
        self.tokens_output += tokens_out

    def log_turn(self, role: str, content: str, meta: dict | None = None):
        self.conversation_log.append({
            "turn": len(self.conversation_log) + 1,
            "role": role,
            "content": content[:2000],
            "meta": meta or {},
            "wall_offset_s": round(time.perf_counter() - self.start_wall, 3),
        })

    def finish(self):
        self.end_wall = time.perf_counter()
        self.sample_ram()

    def to_dict(self) -> dict:
        return {
            "timestamp": datetime.now().isoformat(),
            "framework": self.framework,
            "model": self.model,
            "ttfr_s": self.ttfr,
            "total_time_s": round((self.end_wall or time.perf_counter()) - self.start_wall, 3),
            "llm_rounds": self.llm_rounds,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_input + self.tokens_output,
            "ram_peak_mb": max(self.ram_samples) if self.ram_samples else 0,
            "quality": self.quality,
            "final_invoice_json": self.final_invoice_json,
            "conversation_log": self.conversation_log,
        }

    def save(self) -> Path:
        slug = re.sub(r"[^\w\-]", "-", self.model)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = RESULTS_DIR / f"{self.framework}_{slug}_{int(time.time())}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        header = "framework,model,ttfr_s,total_time_s,llm_rounds,tokens_input,tokens_output,tokens_total,ram_peak_mb,auto_score,invoice_json_ok,timestamp\n"
        if not SUMMARY_CSV_PATH.exists():
            SUMMARY_CSV_PATH.write_text(header, encoding="utf-8")
        
        result = self.to_dict()
        q = result.get("quality", {})
        row = f"{self.framework},{self.model},{result['ttfr_s']},{result['total_time_s']}," \
              f"{self.llm_rounds},{self.tokens_input},{self.tokens_output},{result['tokens_total']}," \
              f"{result['ram_peak_mb']},{q.get('auto_score_0_5', 0)}," \
              f"{1 if result.get('final_invoice_json') else 0},{result['timestamp']}\n"
        
        with open(SUMMARY_CSV_PATH, "a", encoding="utf-8") as f:
            f.write(row)
            
        return filename