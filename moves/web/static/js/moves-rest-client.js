import { rest_hostname, rest_port } from './configuration.js';

const basename = `https://${rest_hostname}:${rest_port}`

/**
 * @param {string} game_id
 * @param {string} move
 */
const update = async (game_id, move) => {
	const response = await fetch(`${basename}/update`, {
		method: 'POST',
		body: JSON.stringify({
			game_id: game_id,
			move: move
		}),
		headers: {
			'Content-Type': 'application/json'
		}
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
};

const start_new_game = async () => {
	const response = await fetch(`${basename}/start_new_game`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: {}
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
};

export { update, start_new_game };
