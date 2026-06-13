FROM golang:1.24 AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /social ./cmd/server

FROM gcr.io/distroless/static-debian12
WORKDIR /app
COPY --from=build /social /app/social
COPY web /app/web
ENV PORT=8080
EXPOSE 8080
CMD ["/app/social"]
