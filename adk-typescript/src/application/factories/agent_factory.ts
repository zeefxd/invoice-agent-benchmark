import { LlmAgent, FunctionTool } from '@google/adk';
import { Ollama } from 'adk-ollama';
import { InvoiceAgentSystemPrompt } from '../../domain/constants';
import * as validators from '../tools/validators';
import * as calculators from '../tools/calculators';
import * as formatters from '../tools/formatters';

import 'dotenv/config';

function initModel(modelName: string): any {
    if (modelName.startsWith("ollama_chat/")) {
        let actualName = modelName.replace("ollama_chat/", "");

        if (actualName.endsWith(":cloud")) {
            actualName = actualName.replace(":cloud", "");
            console.log(`[FACTORY] Podłączanie chmurowego modelu Ollama: ${actualName}`);

            const apiKey = process.env.OLLAMA_API_KEY;
            if (!apiKey) {
                throw new Error("missing OLLAMA_API_KEY for cloud model");
            }

            return new Ollama({
                model: actualName,
                baseUrl: process.env.OLLAMA_CLOUD_URL || "https://ollama.com",
                apiKey: apiKey,
            } as any);
        }

        console.log(`[FACTORY] Podłączanie lokalnego modelu Ollama: ${actualName}`);
        return new Ollama({
            model: actualName,
            baseUrl: process.env.OLLAMA_LOCAL_URL || "http://localhost:11434"
        });
    }

    throw new Error(`unsupported model: ${modelName}`);
}

export function buildAgent(modelIdentifier: string): LlmAgent {
    const selectedModel = initModel(modelIdentifier);

    const validateNipTool = new FunctionTool({
        name: "validate_nip",
        description: "Sprawdza poprawność numeru NIP",
        parameters: {
            type: "object",
            properties: {
                nip: { type: "string" }
            }
        } as any,
        execute: async (args: any) => {
            return validators.validateNip(args.nip);
        }
    });

    const calculateLineTool = new FunctionTool({
        name: "calculate_line",
        description: "Oblicza kwoty pozycji",
        parameters: {
            type: "object",
            properties: {
                quantity: { type: "number" },
                unit_price_net: { type: "number" },
                vat_rate: { type: "string" }
            }
        } as any,
        execute: async (args: any) => {
            return calculators.calculateLine(args.quantity, args.unit_price_net, args.vat_rate);
        }
    });

    const calculateTotalsTool = new FunctionTool({
        name: "calculate_totals",
        description: "Oblicza sumy faktury",
        parameters: {
            type: "object",
            properties: {
                lines: {
                    type: "array",
                    items: { type: "object" }
                }
            }
        } as any,
        execute: async (args: any) => {
            return calculators.calculateTotals(args.lines);
        }
    });

    const formatInvoiceTool = new FunctionTool({
        name: "format_invoice",
        description: "Formatuje gotowy JSON faktury",
        parameters: {
            type: "object",
            properties: {
                data: { type: "object" }
            }
        } as any,
        execute: async (args: any) => {
            return formatters.formatInvoice(args.data);
        }
    });

    return new LlmAgent({
        name: "invoice_agent",
        model: selectedModel,
        instruction: InvoiceAgentSystemPrompt,
        tools: [validateNipTool, calculateLineTool, calculateTotalsTool, formatInvoiceTool]
    });
}