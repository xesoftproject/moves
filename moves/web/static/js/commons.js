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


export { queryparams, get_query_param, sleep };
