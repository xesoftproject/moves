const STEP = .06;


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
const move = ({ move, table }) => {
	// TODO convert to use table ?
	if (!move)
		return;

	const from = move.substr(0, 2);
	const to = move.substr(2, 2);

	const piece = lookup(from);
	const { delta_x, delta_y } = movement(from, to);

	apply_move(piece, delta_x, delta_y);
};

const init_pieces_position = () => {
	setTimeout(move.bind(this, { move: 'e2e4' }), 5000);
};


const main = () => {
	document.addEventListener('DOMContentLoaded', init_pieces_position);
};

main();
