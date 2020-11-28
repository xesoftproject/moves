# reuse ActiveMQ queues

For the current status of AMQ queues vs topics vs virtual topics the simplest
and more reiable solution found is to use a virtual topic AND ALSO to avoid the
ack on the messages

note over Player1, Player2: subscribe(/queue/Consumer.$uuid.VirtualTopic.$game_id)\npublish(VirtualTopic.$game_id, $mossa)

