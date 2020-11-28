import { REST_PROTOCOL, REST_HOSTNAME, REST_PORT } from './configuration.js';

const basename = `${REST_PROTOCOL}://${REST_HOSTNAME}:${REST_PORT}`

/**
 * @param {string} game_id
 * @param {string} move
 */
const update = async (game_id, move) => {
	const response = await fetch(`${basename}/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			game_id: game_id,
			move: move
		})
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
		body: JSON.stringify({
		})
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
};

export { update, start_new_game };
