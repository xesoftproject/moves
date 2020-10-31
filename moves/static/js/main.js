import { start_new_game, update } from './moves-rest-client.js';
import { subscribe, unsubscribe } from './moves-stomp-client.js';


/**
 * @param {string} player1
 * @param {string} player2
 */
const init_table = async (player1, player2) => {
	console.log('player1: %o, player2: %o', player1, player2);

	unsubscribe();

	const game_id = await start_new_game();
	console.log('game_id: %o', game_id);

	document.querySelector('h3').textContent = game_id;

	await subscribe(game_id, ({ move, table }) => {
		document.querySelector('pre').textContent = table;

		const li = document.createElement('li');
		li.textContent = move;
		document.querySelector('ul').appendChild(li);
	});

	return game_id;
};

/**
 * @param {string} game_id
 */
const btn_move = (game_id) => {
	const btn = document.querySelector('#move');
	if (btn.__cb)
		btn.removeEventListener('click', __cb);
	const cb = async () => {
		const move = document.querySelector('[type=text]').value;

		await update(game_id, move);
	};
	btn.addEventListener('click', cb);
	btn.__cb = cb;
};

const btn_start_new_game = async () => {
	document.querySelector('#start_new_game').addEventListener('click', async () => {
		const player1 = document.querySelector('[name=player1]:checked').value;
		const player2 = document.querySelector('[name=player2]:checked').value;

		const game_id = await init_table(player1, player2);

		btn_move(game_id);
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', btn_start_new_game);
};

main();
