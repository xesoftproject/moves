'use strict';

// TODO: port inside sources
import { v4 } from 'https://jspm.dev/uuid';

import { HTTP, WS, HOSTNAME, CHAT_PORT } from './configuration.js';
import { messages } from './commons.js';

const HTTP_BASENAME = `${HTTP}://${HOSTNAME}:${CHAT_PORT}`;
const WS_BASENAME = `${WS}://${HOSTNAME}:${CHAT_PORT}`;



/**
 * @returns async interator with the chats
 */
const chats = () => {
	return messages(new WebSocket(`${WS_BASENAME}/chats`));
};

/**
 * create a chat
 * @param {string} chat_id
 */
const create_chat = async (chat_id = v4()) => {
	const response = await fetch(`${HTTP_BASENAME}/chat/${chat_id}`, {
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
 * 
 * @param {string} chat_id the chat id - if not present a new one is created
 * @returns {WebSocket} the chat you have just joined
 */
const chat = (chat_id) => {
	return new WebSocket(`${WS_BASENAME}/chat/${chat_id}`);
};


export { chats, create_chat, chat };
