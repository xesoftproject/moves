import { rest_hostname, rest_port } from './configuration.js';

const basename = `http://${rest_hostname}:${rest_port}`

/**
 * @param {string} game_id
 * @param {string} move
 */
const update = async (game_id, move) => {
	const response = await fetch(`${basename}/update`, {
		method: 'POST',
		body: {
			game_id: game_id,
			move: move
		}
	});

	return await response.text();
};

const start_new_game = async () => {
	const response = await fetch(`${basename}/start_new_game`, {
		method: 'POST'
	});

	return await response.text();
};

export { update, start_new_game };
