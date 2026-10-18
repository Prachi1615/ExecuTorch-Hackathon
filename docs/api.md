# Robot API

Start the robot with `--api` to serve a small HTTP API on port **8765** (all interfaces). It lets another program, such as OpenMind OM1, see what Pip sees and make it act. Without `--api` the robot behaves exactly the same and nothing listens.

## Endpoints

### `GET /state`

```json
{
  "seeing": "banana",
  "score": 0.62,
  "known": ["banana", "mug"],
  "paused": false,
  "event": "I see banana",
  "event_id": 7,
  "time": 1792312345.6
}
```

- `seeing`: the current settled answer: a learned name, `unknown` or `nothing`
- `known`: learned names (excluding the `nothing` baseline)
- `event` / `event_id`: the latest thing that happened. `event_id` increases on every event, so a client can poll and react only to new ones. Events: `I see <name>`, `I see something I don't know`, `nothing in front of me`, `learned <name>`, `forgot everything`, `paused`, `resumed`.

### `POST /gesture`

```json
{"name": "nod"}
```

One of `nod`, `shake`, `curious`, `idle`. Ignored while paused or while another gesture is playing.

### `POST /teach`

```json
{"name": "banana"}
```

Learns whatever is in front of the camera under that name (8 photos, ~6 s), then nods. Without a name it uses "thing N".

### `POST /forget`

Forgets everything except the baseline.

### `POST /pause`

```json
{"paused": true}
```

Omit `paused` to toggle.

All `POST` calls return `{"ok": true}` immediately; the command runs in the robot's next loop iteration.

## Try it

```bash
./run.sh --api
# in another terminal:
curl localhost:8765/state
curl -X POST localhost:8765/gesture -d '{"name":"nod"}'
curl -X POST localhost:8765/teach -d '{"name":"banana"}'   # hold the banana up first
```

## Notes

- If another program uses the webcam microphone, start the robot with `--no-mic` so they don't fight over it.
- There is no authentication. Keep it on a trusted network.
