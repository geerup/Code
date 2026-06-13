# Build a static Go binary, then run it with the web assets. Deploy to Fly.io.
FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /arena ./cmd/server

FROM gcr.io/distroless/static-debian12
WORKDIR /app
COPY --from=build /arena /app/arena
COPY web /app/web
ENV PORT=8080
EXPOSE 8080
CMD ["/app/arena"]
