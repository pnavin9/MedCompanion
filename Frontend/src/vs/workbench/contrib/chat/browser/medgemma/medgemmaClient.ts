export interface IToolSchema {
	name: string;
	description: string;
	inputSchema: {
		type: string;
		properties: Record<string, any>;
		required?: string[];
	};
}

export class MedGemmaClient {
	private serverUrl = 'http://localhost:8000';
	private sessionMap = new Map<string, string>();

	async sendMessage(
		vscodeSessionId: string,
		message: string,
		domain: string = 'general',
		mode: string = 'consult',
		imagePath?: string,
		tools?: IToolSchema[]
	): Promise<string> {

		// Get or create server session
		let serverSessionId = this.sessionMap.get(vscodeSessionId);
		if (!serverSessionId) {
			serverSessionId = await this.createSession();
			this.sessionMap.set(vscodeSessionId, serverSessionId);
		}

		// Call /api/v1/chat
		const response = await fetch(`${this.serverUrl}/api/v1/chat`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				session_id: serverSessionId,
				message: message,
				domain: domain,
				mode: mode,
				image_path: imagePath,
				tools: tools
			})
		});

		const data = await response.json();
		return data.response;
	}

	async sendMessageStream(
		vscodeSessionId: string,
		message: string,
		domain: string = 'general',
		mode: string = 'consult',
		onChunk: (chunk: string) => void,
		signal?: AbortSignal,
		imagePath?: string,
		workspacePath?: string,
		tools?: IToolSchema[]
	): Promise<void> {

		// Get or create server session
		let serverSessionId = this.sessionMap.get(vscodeSessionId);
		if (!serverSessionId) {
			serverSessionId = await this.createSession();
			this.sessionMap.set(vscodeSessionId, serverSessionId);
		}

		// Call /api/v1/chat/stream
		const response = await fetch(`${this.serverUrl}/api/v1/chat/stream`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				session_id: serverSessionId,
				message: message,
				domain: domain,
				mode: mode,
				image_path: imagePath,
				workspace_path: workspacePath,
				tools: tools
			}),
			signal
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		if (!response.body) {
			throw new Error('No response body');
		}

		// Parse Server-Sent Events (SSE)
		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

		try {
			while (true) {
				const { done, value } = await reader.read();

				if (done) {
					break;
				}

				// Decode the chunk and add to buffer
				buffer += decoder.decode(value, { stream: true });

				// Split by double newline to get individual SSE messages
				const lines = buffer.split('\n\n');

				// Keep the last incomplete line in the buffer
				buffer = lines.pop() || '';

				// Process each complete SSE message
				for (const line of lines) {
					if (!line.trim()) {
						continue;
					}

					// Extract data after "data: " prefix
					if (line.startsWith('data: ')) {
						const data = line.substring(6);

						// Check for completion marker
						if (data === '[DONE]') {
							return;
						}

						// Check for error marker
						if (data.startsWith('[ERROR:')) {
							const errorMsg = data.substring(8, data.length - 1); // Remove [ERROR: and ]
							throw new Error(errorMsg);
						}

						// Normal chunk - pass to callback
						onChunk(data);
					}
				}
			}
		} finally {
			reader.releaseLock();
		}
	}

	private async createSession(): Promise<string> {
		const response = await fetch(`${this.serverUrl}/api/v1/sessions`, {  // FIXED: Removed /create
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				title: 'MedGemma Chat Session'  // FIXED: Added title field
			})
		});
		const data = await response.json();
		return data.session_id;
	}
}
