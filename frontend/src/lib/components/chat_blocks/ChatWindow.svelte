<script lang="ts">
    import A2ABubble from '$lib/components/chat_blocks/A2AChannels.svelte';
    import MessageBubble from '$lib/components/chat_blocks/Message.svelte';
    import type { Channel, ChatMessage } from '$lib/types';

    /**
     * A render block represents one unit of output in the chat.
     * Either a regular message bubble, or an A2A negotiation container.
     */
    type Block =
        | { kind: 'message'; msg: ChatMessage }
        | { kind: 'a2a'; channels: Channel[] };

    interface Props {messages: ChatMessage[];}
    let {messages}: Props = $props();

    /**
     * Transforms the flat messages array into an ordered list of render blocks.
     * Consecutive inter-agent messages are collapsed into a single A2A block.
     * Re-runs reactively whenever messages changes.
     */
    const blocks = $derived.by((): Block[] => {
        const result: Block[] = [];
        // Maps channel_id → a2a block, so messages can route back to previous blocks
        const a2aBlockMap = new Map<string, Extract<Block, { kind: 'a2a' }>>();
        // Maps channel_id:agent_pair → channel
        const channelMap = new Map<string, Channel>();

        for (const msg of messages) {
            if (msg.type === 'inter_agent_request' || msg.type === 'inter_agent_response') {
                if (!msg.from || !msg.to) continue;

                const agentPairId = [msg.from, msg.to].sort().join('--');

                // Use channel_id if present, otherwise fall back to positional grouping
                const lastBlock = result[result.length - 1];
                const blockKey = msg.channel_id
                    ?? (lastBlock?.kind === 'a2a'
                        ? [...a2aBlockMap.entries()].find(([, b]) => b === lastBlock)?.[0]
                        : `pos-${result.length}`);

                if (!a2aBlockMap.has(blockKey!)) {
                    const newBlock = { kind: 'a2a' as const, channels: [] };
                    a2aBlockMap.set(blockKey!, newBlock);
                    result.push(newBlock);
                }

                const channelKey = `${blockKey}:${agentPairId}`;
                if (!channelMap.has(channelKey)) {
                    const channel: Channel = {
                        id: agentPairId,
                        participants: [msg.from, msg.to].sort() as [string, string],
                        messages: []
                    };
                    channelMap.set(channelKey, channel);
                    a2aBlockMap.get(blockKey!)!.channels.push(channel);
                }

                channelMap.get(channelKey)!.messages.push(msg);
            } else {
                result.push({ kind: 'message', msg });
            }
        }
        return result;
    });


</script>



<div class="flex flex-col gap-4">
  {#each blocks as block, i (i)}
    {#if block.kind === 'message'}
      <MessageBubble message={block.msg} />
    {:else}
      <A2ABubble channels={block.channels} />
    {/if}
  {/each}
</div>