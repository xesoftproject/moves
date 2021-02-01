'use strict';

import { PATH_CHAT, QUERY_PARAMS_CHAT_ID } from './constants.js';
import { chats, create_chat } from './moves-chat-client.js';

import { I_AM } from './configuration.js'

const onload = async () => {
	document.querySelector('h2').textContent = I_AM;

	document.querySelector('form').addEventListener('submit', async (e) => {
		e.preventDefault();

		await create_chat(document.querySelector('input[name="chat_id"]').value);
	});

	for await (const chat_id of chats()) {
		console.log('[chat_id: %o]', chat_id);

		const a = document.createElement('a');
		a.setAttribute('href', `${PATH_CHAT}?${QUERY_PARAMS_CHAT_ID}=${chat_id}`);
		a.textContent = chat_id;
		const li = document.createElement('li');
		li.appendChild(a);
		document.querySelector('ul').appendChild(li);
	}
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
