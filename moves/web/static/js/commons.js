/**
 * return the query parameters as a multi valued map
 * 
 * @param {Location} location
 * @returns {{string, [string]}}
 */
const queryparams = (location = window.location) => {
	if (!location.search)
		return {};

	const ret = {};

	const search = location.search.substr(1);
	for (const [k, v] of search.split('&').map(kv => kv.split('=', 2))) {
		if (k in ret)
			ret[k].push(v);
		else
			ret[k] = [v];
	}

	return ret;
};

/**
 * @param {string} key the key
 * @returns {string} the value
 * @throws {Error} when key not found, or multiple ones
 */
const get_query_param = (key, location = window.location) => {
	const dict = queryparams(location);
	if (!(key in dict))
		throw new Error(`[key: ${key}]`);

	const values = dict[key];
	if (values.length !== 1)
		throw new Error(`[values: ${values}]`);

	return values[0];
};

/**
 * "sleep" async function
 * @param {number} ms - duration
 * @returns {Promise<null>} nothing
 */
const sleep = async (ms) => await new Promise(r => setTimeout(_ => r(null), ms));


/**
 * convert a websocket to an async generator
 * @param {WebSocket} ws
 */
const messages = async function*(ws) {
	let ws_open = ws.readyState === WebSocket.OPEN;
	ws.addEventListener('close', _ => {
		ws_open = false;
	});
	ws.addEventListener('open', _ => {
		ws_open = true;
	});
	ws.addEventListener('error', console.error);
	ws.addEventListener('error', _ => {
		ws_open = false;
	});

	const queue = [];

	ws.addEventListener('message', (event) => queue.push(event.data));

	do {
		const head = queue.shift();
		if (head !== undefined)
			yield Promise.resolve(head);
		else
			await sleep(100);
	}
	while (ws_open);
};


const json_parse = async function*(agen) {
	for await (const el of agen) {
		yield JSON.parse(el);
	}
};


export { queryparams, get_query_param, sleep, messages, json_parse };
