const STEP = .06;

import { subscribe } from './moves-stomp-client.js';
import { queryparams } from './commons.js'
import { GAME_ID } from './constants.js';

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
		delta_x: from_x - to_x,
		delta_y: to_y - from_y
	};
};


/**
 * @param {Element} piece
 * @param {number} delta_x
 * @param {number} delta_y
 */
const apply_move = (piece, delta_x, delta_y) => {
	// the table is rotated of 270°
	const x = piece.object3D.position.x - (delta_y * STEP);
	const y = piece.object3D.position.y
	const z = piece.object3D.position.z + (delta_x * STEP);

	piece.setAttribute('animation', `property: position; dur: 500; to: ${x} ${y} ${z}`);
};


/**
 * @param {{move: ?string, table: string}}
 */
const move = ({ move }) => {
	if (!move)
		return;

	const from = move.substr(0, 2);
	const to = move.substr(2, 2);

	const piece = lookup(from);
	const { delta_x, delta_y } = movement(from, to);

	apply_move(piece, delta_x, delta_y);
};


/**
 * @param {Location} location
 */
const init = async () => {
	// page requirement: ?game_id=xxx
	const game_id = queryparams()[GAME_ID][0];
	if (!game_id) {
		location.replace('index.html?error=nogameid');
		throw new Error();
	}

	console.log('game_id: %o', game_id);

	await subscribe(game_id, move);
};


const main = () => {
	document.addEventListener('DOMContentLoaded', init.bind(undefined));
};


main();
