FROM node:22-alpine AS frontend-build

WORKDIR /build
COPY package.json package-lock.json tsconfig.json vite.config.ts index.html ./
COPY frontend ./frontend
RUN npm ci && npm run build

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY --from=frontend-build /build/dist ./dist
COPY --from=gateway fnpqnn_gateway_mvp /gateway/fnpqnn_gateway_mvp

RUN pip install --no-cache-dir ".[alpha]"

ENV FFED_QLC_STATIC_DIR=/app/dist \
    FFED_QLC_DATA_DIR=/data \
    FFED_QLC_GATEWAY_ROOT=/gateway

ENTRYPOINT ["ffed-qlc"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]

