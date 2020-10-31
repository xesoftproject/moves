import { subscribe } from './moves-stomp-client';

const main = () => {
	document.addEventListener("DOMContentLoaded", () => {
		subscribe((body) => {
			const li = document.createElement('li');
			li.textContent = body;

			document.querySelector('ul').appendChild(li);
		});
	});
};

main();
