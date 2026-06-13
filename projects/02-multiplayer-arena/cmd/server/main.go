// Command server runs the arena: an HTTP server that upgrades /ws connections
// to WebSocket, registers them with the hub, and serves the static client.
//
//	go run ./cmd/server          # http://localhost:8080
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"sync/atomic"

	"github.com/gorilla/websocket"
	"github.com/portfolio/arena/internal/game"
	"github.com/portfolio/arena/internal/hub"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(*http.Request) bool { return true }, // demo: allow all origins
}

var nextID atomic.Uint64

// wsClient adapts a WebSocket connection to the hub.Client interface. Outbound
// writes are serialized through a buffered channel + single writer goroutine.
type wsClient struct {
	id   string
	name string
	conn *websocket.Conn
	out  chan []byte
	once sync.Once
}

func (c *wsClient) ID() string   { return c.id }
func (c *wsClient) Name() string { return c.name }
func (c *wsClient) Send(b []byte) {
	select {
	case c.out <- b:
	default: // drop if the client is too slow — keeps the tick loop non-blocking
	}
}

func (c *wsClient) writePump() {
	for b := range c.out {
		if err := c.conn.WriteMessage(websocket.TextMessage, b); err != nil {
			return
		}
	}
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	world := game.NewWorld(900, 600, 12, 0)
	h := hub.New(world)
	stop := make(chan struct{})
	go h.Run(30, stop)

	http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			return
		}
		id := "p" + strconv.FormatUint(nextID.Add(1), 10)
		name := r.URL.Query().Get("name")
		if name == "" {
			name = id
		}
		c := &wsClient{id: id, name: name, conn: conn, out: make(chan []byte, 8)}
		go c.writePump()
		h.Register(c)
		// Tell the client its own id.
		hello, _ := json.Marshal(map[string]any{"type": "hello", "id": id})
		c.Send(hello)

		defer func() {
			h.Unregister(id)
			c.once.Do(func() { close(c.out) })
			conn.Close()
		}()
		for {
			_, data, err := conn.ReadMessage()
			if err != nil {
				return
			}
			var in struct {
				DX float64 `json:"dx"`
				DY float64 `json:"dy"`
			}
			if json.Unmarshal(data, &in) == nil {
				h.Input(id, in.DX, in.DY)
			}
		}
	})

	http.Handle("/", http.FileServer(http.Dir("web")))
	log.Printf("arena listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
