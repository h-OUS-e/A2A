export type MessageType =
	| 'user'
	| 'inter_agent_request'
	| 'inter_agent_response'
	| 'final_response';

export interface ChatMessage {
	id: string;
	type: MessageType;
	content: string;
	from: string;
	to: string;
	timestamp: number;
}

export interface Channel {
	id: string;
	participants: [string, string];
	messages: ChatMessage[];
}

// export const AGENT_COLORS: Record<string, string> = {
// 	person_a_scheduling_agent: '#3B82F6',
// 	person_b: '#10B981',
// 	person_c: '#F59E0B',
// 	human: '#6366F1'
// };

// export const AGENT_NAMES: Record<string, string> = {
// 	person_a_scheduling_agent: 'Person A (Alex)',
// 	person_b: 'Person B (Jordan)',
// 	person_c: 'Person C (Sam)',
// 	human: 'You'
// };
