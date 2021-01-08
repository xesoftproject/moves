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
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));


/**
 * convert a websocket to an async generator
 * @param {WebSocket} ws
 */
const messages = async function*(ws) {
	if (ws.readyState !== WebSocket.OPEN)
		await new Promise((resolve, reject) => {
			ws.addEventListener('close', reject);
			ws.addEventListener('open', resolve);
			ws.addEventListener('error', reject);
		});

	const datas = [];
	const resolves = [];

	ws.addEventListener('message', (event) => {
		if (resolves.length) {
			resolves.shift()(event.data);
			return;
		}

		datas.push(event.data);
	});

	const receive = () => {
		if (datas.length)
			return Promise.resolve(datas.shift());

		return new Promise(resolve => {
			resolves.push(resolve);
		});
	};

	while (ws.readyState === WebSocket.OPEN) {
		yield await receive();
	}
};


const json_parse = async function*(agen) {
	for await (const el of agen) {
		yield JSON.parse(el);
	}
};


export { queryparams, get_query_param, sleep, messages, json_parse };
