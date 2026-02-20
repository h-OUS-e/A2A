<script lang="ts">
    import MessageBubble from '$lib/components/chat_blocks/Message.svelte';
    import type { ChatMessage } from '$lib/types';
    import { agentColor } from '$lib/utils_agent';

    // Declaring the component's inputs
    // Defining property types
    interface Props {
        messages: ChatMessage[];
        participants: [string, string]; // Each chat window has only 2 participants for now
    }

    // Referencing the props passed to the component
    let { messages, participants }: Props = $props();    

</script>

<div class="w-80 flex-none flex flex-col rounded-lg border border-gray-700 bg-gray-800">
  <header class="flex items-center gap-2 border-b border-gray-700 px-4 py-3">
    <span class="text-xs font-semibold truncate" style="color: {agentColor(participants[0])}">
      {participants[0]}
    </span>
    <span class="text-xs text-gray-500 flex-shrink-0">↔</span>
    <span class="text-xs font-semibold truncate" style="color: {agentColor(participants[1])}">
      {participants[1]}
    </span>
  </header>

  <div class="flex flex-col gap-2 px-4 py-4">
    {#each messages as msg (msg.id)}
      <MessageBubble message={msg} />
    {/each}
  </div>
</div>