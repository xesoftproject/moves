import { rest_hostname, rest_port } from './configuration.js';

const basename = `http://${rest_hostname}:${rest_port}`

const update = async (move) => {
	const response = await fetch(`${basename}/update`, {
		method: 'POST',
		body: move
	});

	const data = await response.text();

	return data;
};

export { update };
