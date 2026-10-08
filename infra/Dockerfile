# One image: the web app is built, then served by the API. Build from the repository root:
#   docker build -f infra/Dockerfile -t stormsense .
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY --from=web /web/dist ./static
ENV STORMSENSE_MODE=mock DATABRICKS_APP_PORT=8000
EXPOSE 8000
USER nobody
CMD ["python", "-m", "app.main"]
