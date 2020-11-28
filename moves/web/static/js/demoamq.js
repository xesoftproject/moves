import { subscribe, publish } from './moves-stomp-client.js';
import { queryparams } from './commons.js';

const GAME_ID = queryparams()['game_id'];
if (!GAME_ID)
	throw new Error('no game_id');

const I_AM = queryparams()['i_am'];
if (!I_AM)
	throw new Error('no i_am');

document.addEventListener('DOMContentLoaded', async () => {
	document.querySelector('h1').textContent = I_AM;
	document.querySelector('button').addEventListener('click', async (e) => {
		e.preventDefault();

		await publish(GAME_ID, `publish - ${I_AM} - ${new Date()}`);
	});

	await subscribe(GAME_ID, (message) => {
		const li = document.createElement('li');
		li.textContent = message;
		document.querySelector('ul').appendChild(li);
	});
});
