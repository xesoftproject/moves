import { HTTP, WS, HOSTNAME, REST_PORT } from './configuration.js';
import { messages } from './commons.js';

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
 * send a move to a game
 * 
 * @param {string} game_id
 * @param {string} move
 * @returns {string} nothing
 */
const update = async (i_am, game_id, move) => {
	const response = await fetch(`${HTTP_BASENAME}/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			i_am: i_am,
			game_id: game_id,
			move: move
		})
	});

	if (!response.ok)
		throw new Error(await response.text());

	return await response.text();
};

/**
 * @returns async interator with the games
 */
const games = () => {
	return messages(new WebSocket(`${WS_BASENAME}/games`));
};

export { update, start_new_game, games };
