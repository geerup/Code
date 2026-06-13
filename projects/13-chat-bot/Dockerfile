# Deploy as a Fly.io worker. No third-party deps — stdlib only.
FROM python:3.11-slim
WORKDIR /app
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["python", "server.py"]
