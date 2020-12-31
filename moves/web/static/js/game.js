'use strict';

const STEP = .06;
const STEP_DURATION = 1000;

import { register } from './moves-rest-client.js';
import { get_query_param } from './commons.js'
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


/**
 * @param {string} from
 * @returns {Element}
 */
const lookup = (from) => {
	return document.querySelector(`[square="${from}"]`);
};


/**
 * @param {string} from
 * @param {string} to
 * @returns {{delta_x: number, delta_y: number}}
 */
const movement = (from, to) => {
	const from_x = from.charCodeAt(0);
	const from_y = parseInt(from.substr(1, 1));
	const to_x = to.charCodeAt(0);
	const to_y = parseInt(to.substr(1, 1));

	return {
		delta_x: to_x - from_x,
		delta_y: to_y - from_y
	};
};


/**
 * @param {Element} piece
 * @param {number} delta_x
 * @param {number} delta_y
 */
const apply_move = async (piece, delta_x, delta_y) => {
	console.log('piece: %o, delta_x: %o, delta_y: %o', piece, delta_x, delta_y);
	if (!piece) {
		console.error('no piece!');
		return;
	}

	// the table is rotated of 90°
	const x = piece.object3D.position.x + (delta_y * STEP);
	const y = piece.object3D.position.y
	const z = piece.object3D.position.z + (delta_x * STEP);

	piece.setAttribute('animation',
		`property: position; dur: ${STEP_DURATION}; to: ${x} ${y} ${z}`);

	await new Promise(r => {
		piece.addEventListener('animationcomplete', () => {
			r(null);
		})
	});
};


const onload = async () => {
	console.log('I_AM', I_AM, 'GAME_ID', GAME_ID);

	const fn = async () => {
		for await (const { move } of register(GAME_ID)) {
			console.log('move: %o', move);

			if (!move)
				continue;

			const from = move.substr(0, 2);
			const to = move.substr(2, 2);

			console.log('from: %o, to: %o', from, to);

			const piece = lookup(from);
			console.log('piece: %o', piece);

			const { delta_x, delta_y } = movement(from, to);
			console.log('delta_x: %o, delta_y: %o', delta_x, delta_y);

			await apply_move(piece, delta_x, delta_y);

			piece.setAttribute('square', to);
		}
	};

	const scene = document.querySelector('a-scene');
	if (scene.hasLoaded)
		await fn();
	else
		scene.addEventListener('loaded', fn);
};


const main = () => {
	document.addEventListener('DOMContentLoaded', onload);
};


main();
