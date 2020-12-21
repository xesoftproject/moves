import { queryparams } from './commons.js';
import { QUERY_PARAMS_I_AM, QUERY_PARAMS_CHAT_ID } from './constants.js';
import { chat } from './moves-chat-client.js';

// TODO identify the user by cookie / hw analysis
const I_AM = queryparams()[QUERY_PARAMS_I_AM][0];
if (!I_AM) {
	window.alert('no I_AM!');
	throw new Error();
}

const CHAT_ID = queryparams()[QUERY_PARAMS_CHAT_ID][0];
if (!CHAT_ID) {
	window.alert('no CHAT_ID!');
	throw new Error();
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

	document.querySelector('button').addEventListener('click', (e) => {
		e.preventDefault();

		ws_chat.send(JSON.stringify({
			from_: I_AM,
			body: document.querySelector('input').value
		}));
	});
});
