<!--
Simple text input with send button
 -->
<script lang="ts">
	let { onsend, disabled = false }: { onsend: (text: string) => void; disabled: boolean } =
		$props();

	let input = $state('');

	function handleSubmit() {
		const text = input.trim();
		if (!text || disabled) return;
		onsend(text);
		input = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}
</script>

<form onsubmit={handleSubmit} class="flex gap-2">
	<input
		type="text"
		bind:value={input}
		onkeydown={handleKeydown}
		placeholder="Send a message to the scheduling agents..."
		{disabled}
		class="flex-1 rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-white placeholder-gray-400 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
	/>
	<button
		type="submit"
		disabled={disabled || !input.trim()}
		class="rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-indigo-600"
	>
		Send
	</button>
</form>
