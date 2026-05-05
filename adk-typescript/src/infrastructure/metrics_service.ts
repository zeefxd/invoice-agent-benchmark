import * as fs from 'fs';
import * as path from 'path';
import { getResultsDir, getSummaryCsvPath } from '../domain/config';

export class MetricsService {
    public model: string;
    public framework: string;
    public startWall: number;
    public endWall: number | null = null;
    public ttfr: number | null = null;
    public llmRounds: number = 0;
    public tokensInput: number = 0;
    public tokensOutput: number = 0;
    public ramSamples: number[] = [];
    public conversationLog: any[] = [];
    public finalInvoiceJson: any = null;
    public quality: any = {};

    constructor(model: string) {
        this.model = model;
        this.framework = 'adk-typescript';
        this.startWall = Date.now();
    }

    public sampleRam(): void {
        const mem = process.memoryUsage();
        this.ramSamples.push(Math.round(mem.rss / 1024 / 1024));
    }

    public recordFirstResponse(): void {
        if (this.ttfr === null) {
            this.ttfr = (Date.now() - this.startWall) / 1000.0;
        }
    }

    public recordLlmCall(tokensIn: number, tokensOut: number): void {
        this.llmRounds++;
        this.tokensInput += tokensIn;
        this.tokensOutput += tokensOut;
    }

    public logTurn(role: string, content: string, meta: any = {}): void {
        let safeContent = content;
        if (safeContent && safeContent.length > 2000) {
            safeContent = safeContent.substring(0, 2000);
        }
        
        this.conversationLog.push({
            turn: this.conversationLog.length + 1,
            role: role,
            content: safeContent,
            meta: meta,
            wall_offset_s: (Date.now() - this.startWall) / 1000.0
        });
    }

    public finish(): void {
        this.endWall = Date.now();
        this.sampleRam();
    }

    public toDict(): any {
        const maxRam = this.ramSamples.length > 0 ? Math.max(...this.ramSamples) : 0;
        const totalTimeS = this.endWall ? (this.endWall - this.startWall) / 1000.0 : 0;
        
        return {
            timestamp: new Date().toISOString(),
            framework: this.framework,
            model: this.model,
            ttfr_s: this.ttfr || 0,
            total_time_s: totalTimeS,
            llm_rounds: this.llmRounds,
            tokens_input: this.tokensInput,
            tokens_output: this.tokensOutput,
            tokens_total: this.tokensInput + this.tokensOutput,
            ram_peak_mb: maxRam,
            quality: this.quality,
            final_invoice_json: this.finalInvoiceJson,
            conversation_log: this.conversationLog
        };
    }

    public save(): string {
        const data = this.toDict();
        const resultsDir = getResultsDir();
        
        if (!fs.existsSync(resultsDir)) {
            fs.mkdirSync(resultsDir, { recursive: true });
        }

        const slug = this.model.replace(/\//g, '-').replace(/:/g, '-');
        const timestamp = Math.floor(Date.now() / 1000);
        const filename = path.join(resultsDir, `${this.framework}_${slug}_${timestamp}.json`);

        fs.writeFileSync(filename, JSON.stringify(data, null, 2), 'utf-8');

        const csvPath = getSummaryCsvPath();
        const header = "framework,model,ttfr_s,total_time_s,llm_rounds,tokens_input,tokens_output,tokens_total,ram_peak_mb,auto_score,invoice_json_ok,timestamp\n";
        
        if (!fs.existsSync(csvPath)) {
            fs.writeFileSync(csvPath, header, 'utf8');
        }

        const hasJson = this.finalInvoiceJson ? 1 : 0;
        const autoScore = this.quality && this.quality.auto_score_0_5 ? this.quality.auto_score_0_5.toFixed(2) : '0.00';
        const ttfr_s = (data.ttfr_s).toFixed(3);
        const total_time_s = (data.total_time_s).toFixed(3);
        
        const row = `${data.framework},${data.model},${ttfr_s},${total_time_s},${data.llm_rounds},${data.tokens_input},${data.tokens_output},${data.tokens_total},${data.ram_peak_mb},${autoScore},${hasJson},${data.timestamp}\n`;
        
        fs.appendFileSync(csvPath, row, 'utf8');
        
        return filename;
    }
}