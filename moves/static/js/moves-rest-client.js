import { rest_hostname, rest_port } from './configuration.js';

const basename = `http://${rest_hostname}:${rest_port}`

const update = async (move) => {
	const response = await fetch(`${basename}/update`, {
		method: 'POST',
		body: move
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
