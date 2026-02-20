<script lang="ts">
  import ChatWindow from '$lib/components/chat_blocks/ChatWindow.svelte';
  import type { ChatMessage } from '$lib/types';

  const messages: ChatMessage[] = [
    { id: '1', type: 'user', content: 'Schedule a meeting with everyone.', from: 'human', to: 'person_a', timestamp: Date.now() },
    { id: '2', type: 'inter_agent_request', content: 'Free Friday 2pm?', from: 'person_a_scheduling_agent', to: 'person_b', timestamp: Date.now() },
    { id: '3', type: 'inter_agent_response', content: 'Yes, works for me.', from: 'person_b', to: 'person_a_scheduling_agent', timestamp: Date.now() },
    { id: '4', type: 'inter_agent_request', content: 'Free Friday 2pm?', from: 'person_a_scheduling_agent', to: 'person_c', timestamp: Date.now() },
    { id: '5', type: 'inter_agent_response', content: 'I have a conflict then.', from: 'person_c', to: 'person_a_scheduling_agent', timestamp: Date.now() },
    { id: '6', type: 'inter_agent_response', content: 'Person B is free but Person C has a conflict on Friday.', from: 'person_d', to: 'human', timestamp: Date.now() },
    { id: '7', type: 'final_response', content: 'Person B is free but Person C has a conflict on Friday.', from: 'person_a_scheduling_agent', to: 'human', timestamp: Date.now() },
    { id: '8', type: 'final_response', content: 'Person B is free but Person C has a conflict on Friday.', from: 'person_a_scheduling_agent', to: 'human', timestamp: Date.now() },
    { id: '9', type: 'user', content: 'Schedule a meeting with everyone.', from: 'human', to: 'person_a', timestamp: Date.now() },

  ];
</script>

<div class="bg-gray-900 min-h-screen p-8">
  <ChatWindow {messages} />
</div>