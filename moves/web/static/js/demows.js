import { WS_PROTOCOL, WS_PORT, AMQ_HOSTNAME } from './configuration.js';
import { queryparams } from './commons.js';

const GAME_ID = queryparams()['game_id'];
if (!GAME_ID)
	throw new Error('no game_id');

const I_AM = queryparams()['i_am'];
if (!I_AM)
	throw new Error('no i_am');




document.addEventListener('DOMContentLoaded', async () => {
	var ws = new WebSocket(`${WS_PROTOCOL}://${AMQ_HOSTNAME}:${WS_PORT}/register/${GAME_ID}`);

	document.querySelector('h1').textContent = I_AM;
	document.querySelector('h2').textContent = GAME_ID;
	document.querySelector('button').addEventListener('click', (e) => {
		e.preventDefault();

		ws.send(`publish - ${I_AM} - ${new Date()}`);
	});

	ws.onmessage = (event) => {
		const li = document.createElement('li');
		li.textContent = event.data;
		document.querySelector('ul').appendChild(li);
	};
});
