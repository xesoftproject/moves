import { start_new_game } from './moves-rest-client.js';

const main = () => {
	document.addEventListener("DOMContentLoaded", () => {
		document.querySelector('button').addEventListener('click', async () => {
			const move = document.querySelector('input').value;

			const game = await start_new_game(move);

			location.replace(`game.html?game=${game}`);
		});
	});
};

main();
