'use strict';

import { start_new_game } from './moves-rest-client.js';

const btn_start_new_game = async () => {
	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const game_id = await start_new_game();
		console.log('game_id: %o', game_id);

		window.open('audio.html?game_id=' + game_id, '_blank');
		window.location.replace(`game.html?game_id=${game_id}`);
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', btn_start_new_game);
};

main();
