import { update, register } from './moves-rest-client.js';
import { get_query_param } from './commons.js';
import { QUERY_PARAMS_I_AM, QUERY_PARAMS_GAME_ID } from './constants.js';


// TODO identify the user by cookie / hw analysis
let I_AM;
try {
	I_AM = get_query_param(QUERY_PARAMS_I_AM);
}
catch (error) {
	window.alert('no I_AM!');
	throw error;
}

// page requirement: ?game_id=xxx
let GAME_ID;
try {
	GAME_ID = get_query_param(QUERY_PARAMS_GAME_ID);
}
catch (error) {
	window.alert('no GAME_ID!');
	throw error;
}

const onload = async () => {
	document.querySelector('h3').textContent = GAME_ID;

	for await (const { table } of register(GAME_ID)) {
		document.querySelector('pre').textContent = table;
	}

	document.querySelector('#move').addEventListener('click', async () => {
		const move = document.querySelector('[type=text]').value;

		try {
			await update(I_AM, game_id, move);
		}
		catch (e) {
			window.alert(e);
		}
	});
};

const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};

main();
