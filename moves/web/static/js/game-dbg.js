'use strict';


import { register } from './moves-rest-client.js';
import { get_query_param } from './commons.js'
import { QUERY_PARAMS_GAME_ID } from './constants.js';
import { I_AM } from './configuration.js'


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
	console.debug('I_AM', I_AM, 'GAME_ID', GAME_ID);

	for await (const { move, table, winner } of register(GAME_ID)) {
		document.querySelector('#table').textContent = table;
		document.querySelector('#winner').textContent = winner;
		const li = document.createElement('li')
		li.textContent = move;
		document.querySelector('#moves').appendChild(li);
	}
};


const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};


main();
