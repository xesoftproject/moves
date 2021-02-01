import { get_query_param } from './commons.js';
import { QUERY_PARAMS_CHAT_ID } from './constants.js';
import { chat } from './moves-chat-client.js';
import { I_AM } from './configuration.js'

let CHAT_ID;
try {
	CHAT_ID = get_query_param(QUERY_PARAMS_CHAT_ID);
}
catch (error) {
	window.alert('no CHAT_ID!');
	throw error;
}

document.addEventListener('DOMContentLoaded', () => {
	document.querySelector('.i_am').textContent = I_AM;
	document.querySelector('.chat_id').textContent = CHAT_ID;

	const ws_chat = chat(CHAT_ID);
	ws_chat.onmessage = (event) => {
		const { from_, body } = JSON.parse(event.data);

		const dt = document.createElement('dt');
		dt.textContent = from_;
		document.querySelector('dl').appendChild(dt);

		const dd = document.createElement('dd');
		dd.textContent = body;
		document.querySelector('dl').appendChild(dd);
	};

	document.querySelector('form').addEventListener('submit', (e) => {
		e.preventDefault();

		ws_chat.send(JSON.stringify({
			from_: I_AM,
			body: document.querySelector('input').value
		}));
	});
});
