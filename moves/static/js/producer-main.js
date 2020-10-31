import { update } from './moves-rest-client';

const main = () => {
	document.addEventListener("DOMContentLoaded", () => {
		document.querySelector('button').addEventListener('click', async () => {
			const move = document.querySelector('input').value;

			const data = await update(move);

			document.querySelector('pre').textContent = data;
		});
	});
};

main();
