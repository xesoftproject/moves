'use strict';

import { get_query_param } from './commons.js';
import { QUERY_PARAMS_I_AM, PATH_GAME, QUERY_PARAMS_GAME_ID } from './constants.js';
import { start_new_game, games } from './moves-rest-client.js';


// TODO identify the user by cookie / hw analysis
let I_AM;
try {
	I_AM = get_query_param(QUERY_PARAMS_I_AM);
}
catch (error) {
	window.alert('no I_AM!');
	throw error;
}

const join = (game_id) => {
	window.open(`audio.html?${QUERY_PARAMS_I_AM}=${I_AM}&${QUERY_PARAMS_GAME_ID}=${game_id}`, '_blank');
	window.location.assign(`${PATH_GAME}?${QUERY_PARAMS_I_AM}=${I_AM}&${QUERY_PARAMS_GAME_ID}=${game_id}`);
}

const onload = async () => {
	document.querySelector('.i_am').textContent = I_AM;

	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const white = document.querySelector('[name="white"]:checked').value;
		const black = document.querySelector('[name="black"]:checked').value;

		const game_id = await start_new_game(I_AM, white, black);
		console.log('game_id: %o', game_id);
	});

	for await (const games_ouput of games()) {
		console.log('[games_ouput: %o]', games_ouput);

		if (games_ouput.op === 'add') {
			const a = document.createElement('a');
			a.setAttribute('href', `#`);
			a.textContent = games_ouput.game_id;
			a.addEventListener('click', (e) => {
				e.preventDefault();
				join(game);
			});
			const span = document.createElement('span');
			span.textContent = games_ouput.full ? 'full - only look' : 'play!';
			const li = document.createElement('li');
			li.setAttribute('id', games_ouput.game_id)
			li.appendChild(a);
			li.appendChild(span);
			document.querySelector('#games').appendChild(li);
		}
		else if (games_ouput.op === 'remove') {
			document.querySelector('#games').removeChild(document.querySelector(`#${games_ouput.game_id}`));
		}
		else if (games_ouput.op === 'update') {
			alert('TODO'); // TODO
		}
		else {
			window.aler(`unknown [games_ouput.op: ${games_ouput.op}]`);
			throw new Error(`unknown [games_ouput.op: ${games_ouput.op}]`);
		}
	}
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
