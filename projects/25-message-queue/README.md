# 📮 Mini Message Queue / Job Broker (#25)

An in-memory message broker with **SQS-style at-least-once delivery**, built in
Go. Publish to a topic; consume a message (it goes *in-flight* with a visibility
timeout); ack it when done. If you don't ack in time, it's **redelivered** —
which is exactly how real job queues guarantee work isn't lost when a worker crashes.

## Semantics
- **FIFO** ready queue per topic.
- **Visibility timeout:** a consumed message is hidden, not deleted. `Ack`
  deletes it; otherwise it reappears after the timeout (with an incremented
  `Deliveries` count, so you can detect poison messages).
- **At-least-once:** a crashed worker's un-acked message is retried.

## Deterministic by design
The clock is injectable (`SetClock`), so redelivery timing is tested **without
`time.Sleep`** — `TestRedeliveryAfterVisibilityTimeout` advances a fake clock
and asserts the message reappears only after the timeout.

## API
```
POST /publish/{topic}    body=message   -> {"id":N}
POST /consume/{topic}                    -> {id, body, deliveries} | 404
POST /ack/{topic}/{id}                   -> {"acked":true}
GET  /stats/{topic}                      -> {ready, in_flight}
```

## Run
```bash
go test ./...
go run ./cmd/broker
```

## What I learned / next
- Visibility-timeout delivery, why at-least-once + idempotent consumers is the
  pragmatic default, and testing time without sleeping.
- Next: dead-letter queues after N deliveries, persistent WAL (reuse #24), and
  long-poll consume.
