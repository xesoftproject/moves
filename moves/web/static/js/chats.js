'use strict';

import { get_query_param } from './commons.js';
import { QUERY_PARAMS_I_AM, PATH_CHAT, QUERY_PARAMS_CHAT_ID } from './constants.js';
import { chats, create_chat } from './moves-chat-client.js';

// TODO identify the user by cookie / hw analysis
let I_AM;
try {
	I_AM = get_query_param(QUERY_PARAMS_I_AM);
}
catch (error) {
	window.alert('no I_AM!');
	throw error;
}


const onload = async () => {
	document.querySelector('h2').textContent = I_AM;

	document.querySelector('button').addEventListener('click', async (e) => {
		e.preventDefault();

		await create_chat(document.querySelector('input').value);
	});

	for await (const chat_id of chats()) {
		console.log('[chat_id: %o]', chat_id);

		const a = document.createElement('a');
		a.setAttribute('href', `${PATH_CHAT}?${QUERY_PARAMS_I_AM}=${I_AM}&${QUERY_PARAMS_CHAT_ID}=${chat_id}`);
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