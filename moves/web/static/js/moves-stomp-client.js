import './lib/stomp.umd.min.js';

import { WS_PROTOCOL, WS_PORT, AMQ_HOSTNAME, AMQ_USERNAME, AMQ_PASSCODE, amq_topic, amq_queue } from './configuration.js';

let _stompClient = null;
/** @returns {Promise<StompJs.Client>} */
const connect = () => {
	if (_stompClient === null)
		return new Promise((resolve, reject) => {
			_stompClient = new StompJs.Client({
				connectHeaders: {
					login: AMQ_USERNAME,
					passcode: AMQ_PASSCODE,
				},
				brokerURL: `${WS_PROTOCOL}://${AMQ_HOSTNAME}:${WS_PORT}`,
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
 * @param {({?string, string}) => void} on_message
 */
const subscribe = async (game_id, on_message) => {
	if (subscription !== null)
		throw new Error('subscription is not null');

	const stompClient = await connect();
	subscription = stompClient.subscribe(amq_queue(game_id), (message) => {
		on_message(JSON.parse(message.body));
	}, { ack: 'client' });
};

const unsubscribe = () => {
	if (subscription === null)
		return;

	subscription.unsubscribe();
	subscription = null;
}

/**
 * @param {string} game_id
 * @param {any} messagee
 * @returns void
 */
const publish = async (game_id, message) => {
	const stompClient = await connect();

	stompClient.publish({
		destination: amq_topic(game_id),
		body: JSON.stringify(message),
		headers: {
			'content-type': 'application/json'
		}
	});
}

export { subscribe, unsubscribe, publish };
