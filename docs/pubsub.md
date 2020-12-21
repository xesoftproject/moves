# Pub/Sub

## simple GCP Pub/Sub-inspired in-memory library

### goal

The goal of the `triopubsub` module is to enable a many-to-many
communication between the various running tasks.

The base goals is to mimic the Google cloud platform Pub/Sub architecture, as in
the following image:

![GCP Pub/Sub](https://cloud.google.com/pubsub/images/many-to-many.svg)


### Esposing interface with websocket

With the help of quart* libraries it has been proven to be easy to expose the
pubsub api in form of websocket.

A simple usecase is the `chat` package.

A similar approach will be used in the `rest` package, to push the moves to
the clients.

### AMQ limitation

The initial idea was to use AMQ to push notification, and rewriting from scratch
is always a difficult task.
But with apacheMQ there were some limitations.
The first and more important is that there was no way to achieve *both*
broadcast (sending the same message to all the clients) and persistence (sending
old messages to a newly connected client).

### features implemented

The messages from a topic should be broadcasted to all the subscriptions:

![Pub/Sub - multiple subscriptions](https://www.websequencediagrams.com/cgi-bin/cdraw?lz=dGl0bGUgUHViL1N1YiAtIG11bHRpcGxlIHN1YnNjcmlwdGlvbnMKCmFjdG9yIHByb2R1Y2VyCnBhcnRpY2lwYW50IHRvcGljIAAGDQAxDDEAARoyAFAHAGUHYmVyMSAAAhEyIAoKAEIOLS0-AG8GOiA8ADIJPgAYDTIABh8AZgUtLT4AgRwOABMYAEgGAIEtDQBtDgpsb29wCiAgIACCGQkgAIEaCm1lc3NhZ2UAGgUAgiYGAGYSABgMAIFeDwCBGwliZXIAGw8AORUyADQaMgBADgAfC2VuZAoK&s=vs2010)


The messages from a subscription should be spread one per subscriber:

![Pub/Sub - multiple subscribers](https://www.websequencediagrams.com/cgi-bin/cdraw?lz=dGl0bGUgUHViL1N1YiAtIG11bHRpcGxlIHN1YnNjcmliZXJzCgphY3RvciBwcm9kdWNlciAKcGFydGljaXBhbnQgdG9waWMABQ4ANQdwdGlvbgA1BwBFCjEgAAIRMiAKCgAoDCAtLT4AUgY6IDwAgQAJPgAcCABABS0tPgBbDQASGDIACx8KbG9vcAogICAAgVUKAHMKbWVzc2FnZQAaBQCBYgYAZREAFwxhbHQARQUgICAAgXcNACsLYmVyMQBKDmVscwBbBgAYHjIAJw9uZAplbmQKCg&s=vs2010)


The topics should remember the messages sent to them, and propagate to the new
subscriptions:

![Pub/Sub - memory](https://www.websequencediagrams.com/cgi-bin/cdraw?lz=dGl0bGUgUHViL1N1YiAtIG1lbW9yeQoKYWN0b3IgcHJvZHVjZXIKcGFydGljaXBhbnQgdG9waWMgAAYNc3Vic2NyaXB0aW9uADQHAAwHYmVyCgoAPwggLT4AOAY6IG1lc3NhZ2UKYWN0aXZhdGUAUAYKbm90ZSBvdmVyACAIc2F2ZWQKCgBVDCAtAD0KPABeCT4KAIESBi0-AIEBDQBgCmRlAF0PAHIJAIExDQB4CgA5DgB7DmJlcgCBAgUAXQ4AgQIMAIEkDgCBDAliZXIAfhUAgjUNCg&s=vs2010)
