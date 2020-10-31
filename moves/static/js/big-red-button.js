import { rest_hostname, rest_port } from './configuration.js';

const main = () => {
	document.addEventListener("DOMContentLoaded", () => {
		document.querySelector('button').addEventListener('click', async () => {
			const move = document.querySelector('input').value;

			const response = await fetch(`http://${rest_hostname}:${rest_port}/update`, {
				method: 'POST',
				body: move
			});

			const data = await response.text();

			document.querySelector('pre').textContent = data;
		});
	});
};

main();
