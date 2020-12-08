'use strict';

import { start_new_game } from './moves-rest-client.js';

const join = (game_id) => {
	window.open('audio.html?game_id=' + game_id, '_blank');
	window.location.replace(`game.html?game_id=${game_id}`);
}

const onload = async () => {
	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const white = document.querySelector('[name="white"]:checked').value;
		const black = document.querySelector('[name="black"]:checked').value;

		const game_id = await start_new_game(white, black);
		console.log('game_id: %o', game_id);

		// TODO create a "join table" flow
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
