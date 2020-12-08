import { queryparams } from './commons.js';
import { QUERY_PARAMS_I_AM, PATH_CHAT, QUERY_PARAMS_CHAT_ID } from './constants.js';
import { chats, create_chat } from './moves-chat-client.js';

// TODO identify the user by cookie / hw analysis
const I_AM = queryparams()[QUERY_PARAMS_I_AM];
if (!I_AM) {
	window.alert('no I_AM!');
	throw new Error();
}

document.addEventListener('DOMContentLoaded', () => {
	document.querySelector('h2').textContent = I_AM;

	const ws_chats = chats();
	ws_chats.onmessage = (event) => {
		const a = document.createElement('a');
		a.setAttribute('href', `${PATH_CHAT}?${QUERY_PARAMS_I_AM}=${I_AM}&${QUERY_PARAMS_CHAT_ID}=${event.data}`);
		a.textContent = event.data;
		const li = document.createElement('li');
		li.appendChild(a);
		document.querySelector('ul').appendChild(li);
	};

	document.querySelector('button').addEventListener('click', async (e) => {
		e.preventDefault();

		await create_chat(document.querySelector('input').value);
	});
});
