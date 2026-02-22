/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { CancellationToken } from '../../../../../base/common/cancellation.js';
import { MarkdownString } from '../../../../../base/common/htmlContent.js';
import { ILogService } from '../../../../../platform/log/common/log.js';
import { IChatProgress } from '../../common/chatService.js';
import { IMcpService, McpConnectionState } from '../../../mcp/common/mcpTypes.js';
import { MedGemmaClient, IToolSchema } from './medgemmaClient.js';

interface IToolCall {
	tool: string;
	args: Record<string, any>;
	rawMatch: string;
}

interface IToolExecutionResult {
	success: boolean;
	result?: any;
	error?: string;
	toolName: string;
}

/**
 * Handles MedGemma's custom tool call format and execution loop
 */
export class MedGemmaToolCallHandler {

	constructor(
		private readonly mcpService: IMcpService,
		private readonly medgemmaClient: MedGemmaClient,
		private readonly logService: ILogService
	) { }

	/**
	 * Process a MedGemma response, detect tool calls, execute them,
	 * and loop back for final response
	 */
	async handleResponse(
		sessionId: string,
		originalMessage: string,
		response: string,
		domain: string,
		mode: string,
		tools: IToolSchema[],
		progress: (part: IChatProgress) => void,
		token: CancellationToken,
		imagePath?: string,
		workspacePath?: string
	): Promise<void> {
		const MAX_ITERATIONS = 5; // Prevent infinite loops
		let currentResponse = response;
		let iteration = 0;

		// Create AbortSignal from CancellationToken
		const abortController = new AbortController();
		const tokenListener = token.onCancellationRequested(() => abortController.abort());

		try {
			while (this.hasToolCalls(currentResponse) && iteration < MAX_ITERATIONS) {
				iteration++;
				this.logService.info(`[MedGemma Tools] Iteration ${iteration}: Tool calls detected`);

				// Extract tool calls
				const toolCalls = this.extractToolCalls(currentResponse);
				this.logService.info(`[MedGemma Tools] Found ${toolCalls.length} tool call(s)`);

				if (toolCalls.length === 0) {
					break;
				}

				// Show tool execution indicator
				progress({
					kind: 'progressMessage',
					content: new MarkdownString(`\n\nExecuting ${toolCalls.length} tool(s)...`)
				});

				// Execute tools
				const results = await this.executeToolCalls(toolCalls);

				// Format results for LLM
				const toolResultsText = this.formatResultsForLLM(toolCalls, results);

				this.logService.info(`[MedGemma Tools] Tool results:`, toolResultsText);

				// Send results back to LLM for natural language response
				progress({
					kind: 'progressMessage',
					content: new MarkdownString('Generating response with tool results...')
				});

				// Build message with tool results
				const followUpMessage = `${this.stripToolCalls(currentResponse)}\n\n[Tool Results]\n${toolResultsText}\n\nBased on these results, provide a natural language answer to the user's question.`;

				// Get LLM response with tool results
				currentResponse = '';
				await this.medgemmaClient.sendMessageStream(
					sessionId,
					followUpMessage,
					domain,
					mode,
					(chunk: string) => {
						currentResponse += chunk;
						progress({
							kind: 'markdownContent',
							content: new MarkdownString(chunk)
						});
					},
					abortController.signal,
					imagePath,
					workspacePath,
					tools
				);
			}

			if (iteration >= MAX_ITERATIONS) {
				this.logService.warn('[MedGemma Tools] Max iterations reached, stopping tool execution loop');
			}
		} finally {
			tokenListener.dispose();
		}
	}

	/**
	 * Parse MedGemma's custom tool call format
	 * Format: tool_code{"tool": "multiply", "args": {"numbers": [18.7, 0.015, 42.3]}}
	 */
	private extractToolCalls(text: string): IToolCall[] {
		const toolCalls: IToolCall[] = [];
		const regex = /tool_code\s*/g;
		let match: RegExpExecArray | null;

		while ((match = regex.exec(text)) !== null) {
			const startPos = match.index + match[0].length;
			const jsonStr = this.extractJsonObject(text, startPos);

			if (jsonStr) {
				try {
					const parsed = JSON.parse(jsonStr);

					if (parsed.tool && parsed.args) {
						toolCalls.push({
							tool: parsed.tool,
							args: parsed.args,
							rawMatch: match[0] + jsonStr
						});
					}
				} catch (error) {
					this.logService.warn('[MedGemma Tools] Failed to parse tool call:', jsonStr, error);
				}
			}
		}

		return toolCalls;
	}

	/**
	 * Extract a complete JSON object from text, handling nested braces
	 */
	private extractJsonObject(text: string, startPos: number): string | null {
		let braceCount = 0;
		let inString = false;
		let escapeNext = false;
		let jsonStr = '';

		for (let i = startPos; i < text.length; i++) {
			const char = text[i];
			jsonStr += char;

			if (escapeNext) {
				escapeNext = false;
				continue;
			}

			if (char === '\\') {
				escapeNext = true;
				continue;
			}

			if (char === '"') {
				inString = !inString;
				continue;
			}

			if (!inString) {
				if (char === '{') {
					braceCount++;
				} else if (char === '}') {
					braceCount--;
					if (braceCount === 0) {
						return jsonStr;
					}
				}
			}
		}

		return null;
	}

	private hasToolCalls(text: string): boolean {
		return /tool_code\s*\{/.test(text);
	}

	private stripToolCalls(text: string): string {
		const toolCalls = this.extractToolCalls(text);
		let cleanText = text;

		for (const toolCall of toolCalls) {
			cleanText = cleanText.replace(toolCall.rawMatch, '');
		}

		return cleanText.trim();
	}

	/**
	 * Execute tool calls via MCP
	 */
	private async executeToolCalls(toolCalls: IToolCall[]): Promise<IToolExecutionResult[]> {
		const results: IToolExecutionResult[] = [];

		for (const toolCall of toolCalls) {
			const result = await this.executeToolCall(toolCall);
			results.push(result);
		}

		return results;
	}

	private async executeToolCall(toolCall: IToolCall): Promise<IToolExecutionResult> {
		this.logService.info(`[MedGemma Tools] Executing tool: ${toolCall.tool}`, toolCall.args);

		try {
			const servers = this.mcpService.servers.get();

			for (const server of servers) {
				const tools = server.tools.get();
				const tool = tools.find((t: any) => t.definition.name === toolCall.tool);

				if (tool) {
					this.logService.info(`[MedGemma Tools] Found tool ${toolCall.tool} in server ${server.definition.id}`);

					// Ensure server is started
					const state = await server.start();
					if (state.state !== McpConnectionState.Kind.Running) {
						throw new Error(`Server failed to start: ${McpConnectionState.toKindString(state.state)}`);
					}

					// Execute the tool
					const result = await tool.call(toolCall.args, CancellationToken.None);

					this.logService.info(`[MedGemma Tools] Tool ${toolCall.tool} executed successfully`);

					return {
						success: true,
						result: result,
						toolName: toolCall.tool
					};
				}
			}

			// Tool not found
			const error = `Tool "${toolCall.tool}" not found`;
			this.logService.error(`[MedGemma Tools] ${error}`);
			return {
				success: false,
				error,
				toolName: toolCall.tool
			};

		} catch (error) {
			const errorMsg = error instanceof Error ? error.message : String(error);
			this.logService.error(`[MedGemma Tools] Failed to execute tool ${toolCall.tool}:`, error);
			return {
				success: false,
				error: errorMsg,
				toolName: toolCall.tool
			};
		}
	}

	/**
	 * Format tool results for sending back to LLM
	 */
	private formatResultsForLLM(toolCalls: IToolCall[], results: IToolExecutionResult[]): string {
		const formatted = toolCalls.map((call, index) => {
			const result = results[index];
			if (result.success) {
				// Extract text content from MCP response
				let value = '';
				if (result.result && typeof result.result === 'object') {
					if (Array.isArray(result.result.content)) {
						value = result.result.content
							.map((item: any) => item.type === 'text' ? item.text : JSON.stringify(item))
							.join('\n');
					} else {
						value = JSON.stringify(result.result);
					}
				} else {
					value = String(result.result);
				}
				return `${call.tool}(${JSON.stringify(call.args)}) = ${value}`;
			} else {
				return `${call.tool}(${JSON.stringify(call.args)}) = ERROR: ${result.error}`;
			}
		}).join('\n');

		return formatted;
	}
}
