FROM node:18-alpine

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY services/ui/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY services/ui .

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
