// TODO: port inside sources
import { v4 } from 'https://jspm.dev/uuid';

import { WS, HTTP, HOSTNAME, CHAT_PORT } from './configuration.js';

/**
 * @returns {WebSocket} the chats
 */
const chats = () => {
	return new WebSocket(`${WS}://${HOSTNAME}:${CHAT_PORT}/chats`);
};

/**
 * create a chat
 * @param {string} chat_id
 */
const create_chat = async (chat_id = v4()) => {
	const response = await fetch(`${HTTP}://${HOSTNAME}:${CHAT_PORT}/chat/${chat_id}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		}
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
}

/**
 * join a chat
 * @param {string} chat_id the chat id - if not present a new one is created
 * @returns {WebSocket} the chat you have just joined
 */
const chat = (chat_id) => {
	return new WebSocket(`${WS}://${HOSTNAME}:${CHAT_PORT}/chat/${chat_id}`);
};


export { chats, create_chat, chat };
