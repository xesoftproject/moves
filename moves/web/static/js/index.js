'use strict';

import { get_query_param } from './commons.js';
import { QUERY_PARAMS_I_AM } from './constants.js';
import { start_new_game, games, players } from './moves-rest-client.js';


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
	window.open('audio.html?game_id=' + game_id, '_blank');
	window.location.replace(`game.html?game_id=${game_id}`);
}

const onload = async () => {
	document.querySelector('.i_am').textContent = I_AM;

	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const white = document.querySelector('[name="white"]:checked').value;
		const black = document.querySelector('[name="black"]:checked').value;

		const game_id = await start_new_game(white, black);
		console.log('game_id: %o', game_id);
	});

	const ws_games = games();
	ws_games.addEventListener('open', (event) => {
		console.log('open(event: %o)', event);
	});
	ws_games.addEventListener('message', (event) => {
		console.log('message(event: %o)', event);

		const a = document.createElement('a');
		a.setAttribute('href', `#`);
		a.textContent = event.data;
		a.addEventListener('click', (e) => {
			e.preventDefault();
			join(event.data);
		});
		const li = document.createElement('li');
		li.appendChild(a);
		document.querySelector('#games').appendChild(li);
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
