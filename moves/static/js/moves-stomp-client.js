import './lib/stomp.umd.min.js';

import { amq_username, amq_passcode, amq_hostname, ws_port, amq_queue } from './configuration.js';

let stompClient;

const subscribe = (on_message) => {
	stompClient = new StompJs.Client({
		connectHeaders: {
			login: amq_username,
			passcode: amq_passcode,
		},
		brokerURL: `wss://${amq_hostname}:${ws_port}`,
		debug: (str) => {
			console.log('STOMP: ' + str);
		},
		reconnectDelay: 200,
		onConnect: (frame) => {
			console.log('onConnect: %o', frame);

			stompClient.subscribe(amq_queue, (message) => {
				console.log('got %o', message.body);

				on_message(message.body);

				message.ack();
			}, {
				ack: 'client'
			});
		}
	});

	stompClient.activate();
};

export { subscribe };
