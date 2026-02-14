/*
This script sits as a proxy between browser clients and Person A's A2A server.
It translates chat messages from the browser into JSON-RPC requests for the A2A server, 
and then re-emits the streaming responses as Server-Sent Events (SSE) back to the browser.

Browser  ──POST {message}──>  SvelteKit +server.ts  ──JSON-RPC──>  Person A (port 10001)
Browser  <──SSE events─────  SvelteKit +server.ts  <──SSE──────  Person A (port 10001)
*/
import { v4 as uuidv4 } from 'uuid';
import type { RequestHandler } from './$types';

const A2A_URL = 'http://localhost:10001';

export const POST: RequestHandler = async ({ request }) => {
	const { message } = await request.json();

	// Build JSON-RPC request for A2A message/stream
	const jsonRpcRequest = {
		jsonrpc: '2.0',
		id: uuidv4(),
		method: 'message/stream',
		params: {
			message: {
				role: 'user',
				parts: [{ type: 'text', text: message }],
				messageId: `msg-${Date.now()}`
			},
			configuration: {
				acceptedOutputModes: ['text']
			},
			metadata: {
				sender: 'human'
			}
		}
	};

	// Send to Person A's A2A server
	let a2aResponse: Response;
	try {
		a2aResponse = await fetch(A2A_URL, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(jsonRpcRequest)
		});
	} catch (err) {
		console.error('Cannot reach A2A server:', err);
		return new Response(
			JSON.stringify({ error: `Cannot reach A2A server at ${A2A_URL}. Is the backend running?` }),
			{ status: 502, headers: { 'Content-Type': 'application/json' } }
		);
	}

	if (!a2aResponse.ok || !a2aResponse.body) {
		const body = await a2aResponse.text().catch(() => '');
		console.error('A2A server error:', a2aResponse.status, body);
		return new Response(
			JSON.stringify({ error: `A2A server returned ${a2aResponse.status}: ${body}` }),
			{ status: 502, headers: { 'Content-Type': 'application/json' } }
		);
	}

	// Create a ReadableStream that re-emits parsed events to the browser
	const encoder = new TextEncoder();
	const stream = new ReadableStream({
		async start(controller) {
			const reader = a2aResponse.body!.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			try {
				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					buffer += decoder.decode(value, { stream: true });
					const lines = buffer.split('\n');
					buffer = lines.pop() || '';

					for (const line of lines) {
						if (!line.startsWith('data:')) continue;
						const data = line.slice(5).trim();
						if (!data) continue;

						try {
							const event = JSON.parse(data);

							// Extract from JSON-RPC result
							const result = event.result;
							if (!result) continue;

							const status = result.status;
							if (!status?.message?.parts?.[0]) continue;

							const part = status.message.parts[0];
							const text = part.text || '';
							const fromTo = part.metadata?.from_to || '';
							const state = status.state || 'working';

							// Parse from_to tag: "[person_a -> person_b]"
							let from = '';
							let to = '';
							const match = fromTo.match(/\[(.+?)\s*->\s*(.+?)\]/);
							if (match) {
								from = match[1];
								to = match[2];
							}

							// Determine message type from state + messageId
							const messageId = result.id || status.message.messageId || '';
							let type = 'inter_agent_request';
							if (state === 'completed') {
								type = 'final_response';
							} else if (messageId.startsWith('intermediate-') && from !== to) {
								// Check if it's a response (from != the orchestrator)
								type = from.includes('person_a') ? 'inter_agent_request' : 'inter_agent_response';
							}

							const chatMessage = {
								id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
								type,
								content: text,
								from,
								to,
								timestamp: Date.now()
							};

							controller.enqueue(encoder.encode(`data: ${JSON.stringify(chatMessage)}\n\n`));
						} catch {
							// Skip unparseable lines
						}
					}
				}
			} catch (err) {
				console.error('Stream error:', err);
			} finally {
				controller.enqueue(encoder.encode('data: [DONE]\n\n'));
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			Connection: 'keep-alive'
		}
	});
};
