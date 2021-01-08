'use strict';

import { HTTP, WS, HOSTNAME, REST_PORT } from './configuration.js';
import { messages, json_parse } from './commons.js';

const HTTP_BASENAME = `${HTTP}://${HOSTNAME}:${REST_PORT}`;
const WS_BASENAME = `${WS}://${HOSTNAME}:${REST_PORT}`;

/**
 * @param {string} white
 * @param {string} black
 * @returns {Promise<string>} the game id
 */
const start_new_game = async (user_id, white, black) => {
	const response = await fetch(`${HTTP_BASENAME}/start_new_game`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			'user_id': user_id,
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
 * @returns {Promise<string>} nothing
 */
const update = async (user_id, game_id, move) => {
	const response = await fetch(`${HTTP_BASENAME}/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			user_id: user_id,
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
	return json_parse(messages(new WebSocket(`${WS_BASENAME}/games`)));
};

/**
 * @param {string} game_id
 * @returns async interator with the moves
 */
const register = (game_id) => {
	return json_parse(messages(new WebSocket(`${WS_BASENAME}/register/${game_id}`)));
};

export { update, start_new_game, games, register };
