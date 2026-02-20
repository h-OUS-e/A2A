<script lang="ts">
    import A2AChannel from '$lib/components/chat_blocks/A2AChannel.svelte';
    import type { Channel } from '$lib/types';

    interface Props {
        channels: Channel[];
    }

    let { channels }: Props = $props();
    
</script>

<div class="overflow-x-auto">
    <div class="flex flex-row items-start gap-4 min-w-max">
        {#each channels as channel (channel.id)}
            <A2AChannel 
                messages={channel.messages}
                participants={channel.participants}
            />
        {/each}
    </div>
</div>