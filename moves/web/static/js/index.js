'use strict';

import { PATH_GAME, QUERY_PARAMS_GAME_ID } from './constants.js';
import { start_new_game, games } from './moves-rest-client.js';
import { I_AM } from './configuration.js'

const join = (game_id) => {
	window.open(`audio.html?${QUERY_PARAMS_GAME_ID}=${game_id}`, '_blank');
	window.location.assign(`${PATH_GAME}?${QUERY_PARAMS_GAME_ID}=${game_id}`);
}

const onload = async () => {
	document.querySelector('.i_am').textContent = I_AM;

	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const white = document.querySelector('[name="white"]:checked').value;
		const black = document.querySelector('[name="black"]:checked').value;

		const game_id = await start_new_game(I_AM, white, black);
		console.log('game_id: %o', game_id);
	});

	for await (const { op, game_id, full } of games()) {
		console.log('[op: %o, game_id: %o, full: %o]', op, game_id, full);

		if (op === 'add') {
			const a = document.createElement('a');
			a.setAttribute('href', `#`);
			a.textContent = game_id;
			a.addEventListener('click', (e) => {
				e.preventDefault();
				join(game_id);
			});
			const span = document.createElement('span');
			span.textContent = full ? 'full - only look' : 'play!';
			const li = document.createElement('li');
			li.setAttribute('id', game_id)
			li.appendChild(a);
			li.appendChild(span);
			document.querySelector('#games').appendChild(li);
		}
		else if (op === 'remove') {
			document.querySelector('#games').removeChild(document.querySelector(`#${game_id}`));
		}
		else if (op === 'update') {
			alert('TODO'); // TODO
		}
		else {
			window.alert(`unknown [op: ${op}]`);
			throw new Error(`unknown [op: ${op}]`);
		}
	}
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
