import { HTTP, WS, HOSTNAME, REST_PORT } from './configuration.js';

const HTTP_BASENAME = `${HTTP}://${HOSTNAME}:${REST_PORT}`;
const WS_BASENAME = `${WS}://${HOSTNAME}:${REST_PORT}`;

/**
 * @param {string} white
 * @param {string} black
 * @returns {string} the game id
 */
const start_new_game = async (white, black) => {
	const response = await fetch(`${HTTP_BASENAME}/start_new_game`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			'white': white,
			'black': black
		})
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
};

/**
 * @param {string} game_id
 * @param {string} move
 * @returns {string} nothing
 */
const update = async (game_id, move) => {
	const response = await fetch(`${HTTP_BASENAME}/update`, {
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

/**
 * @returns {WebSocket} the current games playing - read only
 */
const games = () => {
	return new WebSocket(`${WS_BASENAME}/games`);
};

/**
 * @returns {WebSocket} the human connected players - read only
 */
const players = () => {
	return new WebSocket(`${WS_BASENAME}/players`);
};


export { update, start_new_game, games, players };
