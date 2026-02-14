<!--
This component renders a single chat message in the conversation. 

It supports three types of messages:

1. User messages (type: 'user'): 
    These are messages sent by the user. They are displayed on the right
    side with a blue background.
2. Final responses (type: 'final_response'): 
    These are final answers from agents. They are displayed on the left
    side with a gray background and include the agent's name.
3. Inter-agent messages (type: 'inter_agent_request' or 'inter_agent_response'): 
    These are messages exchanged between agents. They are displayed with 
    a colored border indicating the sender and receiver agents.

The component uses a function to generate consistent colors for agents based on
their names, ensuring that messages from the same agent have the same color 
throughout the conversation.
-->
<script lang="ts">
	import type { ChatMessage } from '$lib/types';

	let { message }: { message: ChatMessage } = $props();

	// Generate a consistent color from agent name (hash -> hue)
	function agentColor(name: string): string {
		let hash = 0;
		for (let i = 0; i < name.length; i++) {
			hash = name.charCodeAt(i) + ((hash << 5) - hash);
		}
		const hue = Math.abs(hash) % 360;
		return `hsl(${hue}, 60%, 45%)`;
	}

	const isUser = message.type === 'user';
	const isFinal = message.type === 'final_response';
	const isInterAgent = message.type === 'inter_agent_request' || message.type === 'inter_agent_response';
</script>

{#if isUser}
	<div class="flex justify-end">
		<div class="max-w-[75%] rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2 text-white">
			<p class="whitespace-pre-wrap">{message.content}</p>
		</div>
	</div>
{:else if isInterAgent}
	<div class="ml-4 border-l-2 pl-3" style="border-color: {agentColor(message.from)}">
		<p class="mb-1 text-xs text-gray-400">
			<span style="color: {agentColor(message.from)}">{message.from}</span>
			<span class="mx-1">→</span>
			<span style="color: {agentColor(message.to)}">{message.to}</span>
		</p>
		<p class="whitespace-pre-wrap text-sm text-gray-200">{message.content}</p>
	</div>
{:else if isFinal}
	<div class="flex justify-start">
		<div class="max-w-[85%] rounded-2xl rounded-bl-sm bg-gray-700 px-4 py-2">
			<p class="mb-1 text-xs text-gray-400">{message.from}</p>
			<p class="whitespace-pre-wrap text-gray-100">{message.content}</p>
		</div>
	</div>
{/if}
