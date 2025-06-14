# Используем официальный образ Node.js
FROM node:18-alpine as build

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY package*.json .
RUN npm install

# Копируем исходники и собираем проект
COPY . .
RUN npm run build

# Используем nginx для раздачи статики
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
