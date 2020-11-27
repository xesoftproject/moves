export const rest_protocol = '{{rest_protocol}}';
export const rest_hostname = '{{rest_hostname}}';
export const rest_port = parseInt('{{rest_port}}');
export const stomp_port = parseInt('{{stomp_port}}');
export const ws_port = parseInt('{{ws_port}}');
export const amq_hostname = '{{amq_hostname}}';
export const amq_username = '{{amq_username}}';
export const amq_passcode = '{{amq_passcode}}';
// shared format logic with python
export const amq_queue = (game_id) => `{{amq_queue}}-${game_id}`;
