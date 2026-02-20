<script lang="ts">
	import ChatWindow from '$lib/components/chat_blocks/ChatWindow.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import type { ChatMessage } from '$lib/types';

	let messages = $state<ChatMessage[]>([]); // Reactive state for chat messages
	let loading = $state(false);
	let chatContainer: HTMLElement;

	// Auto-scroll when new messages arrive
	$effect(() => {
		messages.length;
		if (chatContainer) {
			// Tick delay so DOM updates first
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 0);
		}
	});

	async function sendMessage(text: string) {
		// Add user message immediately
		messages.push({
			id: `user-${Date.now()}`,
			type: 'user',
			content: text,
			from: 'human',
			to: 'person_a',
			timestamp: Date.now()
		});

		loading = true;

		try {
			const response = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: text })
			});

			if (!response.ok || !response.body) {
				const errBody = await response.json().catch(() => ({}));
				throw new Error(errBody.error || 'Failed to connect to agent');
			}

			// Read the SSE stream
			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (!line.startsWith('data:')) continue;
					const data = line.slice(5).trim();
					if (!data || data === '[DONE]') continue;

					try {
						const msg: ChatMessage = JSON.parse(data);
						messages.push(msg);
					} catch {
						// Skip unparseable events
					}
				}
			}
		} catch (err) {
			messages.push({
				id: `error-${Date.now()}`,
				type: 'final_response',
				content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
				from: 'system',
				to: 'human',
				timestamp: Date.now()
			});
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex h-screen flex-col bg-gray-900">
	<!-- Header -->
	<header class="border-b border-gray-700 px-6 py-4">
		<h1 class="text-lg font-semibold text-white">A2A Scheduling Chat</h1>
		<p class="text-sm text-gray-400">Talk to the scheduling agents</p>
	</header>

	<!-- Messages -->
	<div bind:this={chatContainer} class="flex-1 overflow-y-auto px-6 py-4">
	<ChatWindow {messages} />

	{#if loading}
		<div class="flex items-center gap-2 text-sm text-gray-400">
		<div class="h-2 w-2 animate-pulse rounded-full bg-indigo-400"></div>
		Agents are negotiating...
		</div>
	{/if}
	</div>

	<!-- Input -->
	<div class="border-t border-gray-700 px-6 py-4">
		<ChatInput onsend={sendMessage} disabled={loading} />
	</div>
</div>
