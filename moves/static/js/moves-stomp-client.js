import './lib/stomp.umd.min.js';

import { amq_username, amq_passcode, amq_hostname, ws_port, amq_queue } from './configuration.js';

let _stompClient = null;
/** @returns {Promise<StompJs.Client>} */
const connect = () => {
	if (_stompClient === null)
		return new Promise((resolve, reject) => {
			_stompClient = new StompJs.Client({
				connectHeaders: {
					login: amq_username,
					passcode: amq_passcode,
				},
				brokerURL: `wss://${amq_hostname}:${ws_port}`,
				debug: (str) => {
					console.log('STOMP: ' + str);
				},
				reconnectDelay: 200,
				onConnect: (_) => {
					resolve(_stompClient);
				},
				onStompError: reject
			});

			_stompClient.activate();
		});

	return Promise.resolve(_stompClient);
};

// there is a different subscription per game
let subscription = null;

/**
 * @param {string} game_id
 * @param {(string, string) => any} on_message
 */
const subscribe = async (game_id, on_message) => {
	if (subscription !== null)
		throw new Error('subscription is not null');

	const stompClient = await connect();

	subscription = stompClient.subscribe(`/topic/${amq_queue(game_id)}`, (message) => {
		on_message(JSON.parse(message.body));
	});
};

const unsubscribe = () => {
	if (subscription === null)
		return;

	subscription.unsubscribe();
	subscription = null;
}

export { subscribe, unsubscribe };
