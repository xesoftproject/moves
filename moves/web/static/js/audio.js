import { update } from './moves-rest-client.js';
import { subscribe } from './moves-stomp-client.js';
import { queryparams } from './commons.js'
import { GAME_ID } from './constants.js';

const init = async () => {
	// page requirement: ?game_id=xxx
	const game_id = queryparams()[GAME_ID][0];
	if (!game_id) {
		location.replace('index.html?error=nogameid');
		throw new Error();
	}

	console.log('game_id: %o', game_id);
	document.querySelector('h3').textContent = game_id;

	await subscribe(game_id, ({ table }) => {
		document.querySelector('pre').textContent = table;
	});

	document.querySelector('#move').addEventListener('click', async () => {
		const move = document.querySelector('[type=text]').value;

		try {
			await update(game_id, move);
		}
		catch (e) {
			alert(e);
		}
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', init.bind(undefined));
};

main();
