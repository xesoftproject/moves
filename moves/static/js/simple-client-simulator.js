// versione 0.0 - semplici spostamenti

/*
 * basic "move $piece of $deltaX position right and of $deltaY up"
 */
function move(piece, deltaX, deltaY) {
	let el = document.querySelector(`a-entity[gltf-model="#${piece}"]`);
	let x = el.object3D.position.x + deltaX;
	let y = el.object3D.position.y
	let z = el.object3D.position.z - deltaY; // z on 3d-plane, y on 2d, mirrored

	el.setAttribute('animation', `property: position; dur: 500; to: ${x} ${y} ${z}`);

	console.log("moving %s to (%o, %o)", piece, x, z);
}

// simula chiamate da websocket con comandi di spostamento (o robe simili)

function simpleClientSimulator() {
	setTimeout(move.bind(this, 'avocado', 1, 1), 500);
	setTimeout(move.bind(this, 'avocado', 1, 2), 1000);
	setTimeout(move.bind(this, 'avocado', -1, 1), 1500);
	setTimeout(move.bind(this, 'buggy', 0, 3), 2000);
	setTimeout(move.bind(this, 'buggy', 3, 0), 2500);
	setTimeout(move.bind(this, 'buggy', 0, -1), 3000);
	setTimeout(move.bind(this, 'duck', 2, 2), 3500);
	setTimeout(move.bind(this, 'duck', 2, 2), 4000);
	setTimeout(move.bind(this, 'duck', -3, -3), 4500);
	setTimeout(move.bind(this, 'suzanne', 1, 3), 5000);
	setTimeout(move.bind(this, 'suzanne', 2, 2), 5500);
	setTimeout(move.bind(this, 'suzanne', 3, 1), 6000);
	setTimeout(move.bind(this, 'avocado', -1, 1), 6500);
	setTimeout(move.bind(this, 'avocado', 1, 0), 7000);
	setTimeout(move.bind(this, 'avocado', 2, -1), 7500);
	setTimeout(move.bind(this, 'buggy', 4, 0), 8000);
	setTimeout(move.bind(this, 'buggy', -2, -2), 8500);
	setTimeout(move.bind(this, 'buggy', 0, 4), 9000);
	setTimeout(move.bind(this, 'duck', 1, 1), 9500);
	setTimeout(move.bind(this, 'duck', 0, 5), 10000);
	setTimeout(move.bind(this, 'duck', -1, -3), 10500);
	setTimeout(move.bind(this, 'suzanne', -1, 1), 11000);
	setTimeout(move.bind(this, 'suzanne', -1, -1), 11500);
	setTimeout(move.bind(this, 'suzanne', -1, 0), 12000);
	setTimeout(move.bind(this, 'avocado', -4, 1), 12500);
	setTimeout(move.bind(this, 'avocado', 2, 0), 13000);
	setTimeout(move.bind(this, 'avocado', 3, -3), 13500);
}

document.addEventListener('DOMContentLoaded', simpleClientSimulator);
