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
        const channelMap = new Map<string, Channel>(); // Tracks known channels so we don't create duplicates

        for (const msg of messages) {
            if (msg.type === 'inter_agent_request' || msg.type === 'inter_agent_response') {
                if (!msg.from || !msg.to) continue;

                // Canonical channel ID: sort participants so a--b === b--a
                const id = [msg.from, msg.to].sort().join('--');

                if (!channelMap.has(id)) {
                    const channel: Channel = {
                        id,
                        participants: [msg.from, msg.to].sort() as [string, string],
                        messages: []
                    };
                    channelMap.set(id, channel);

                    // Append to existing a2a block if one is already at the end,
                    // otherwise start a new a2a block
                    const lastBlock = result[result.length - 1];
                    if (lastBlock && lastBlock.kind === 'a2a') {
                        lastBlock.channels.push(channel);
                    } else {
                        result.push({ kind: 'a2a', channels: [channel] });
                    }
                }
                
                channelMap.get(id)!.messages.push(msg);
            } else {
                result.push({ kind: 'message', msg });
            }
        }
        return result;
    })

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