FROM nginx:1.18
RUN rm -rf /usr/share/nginx/*
RUN mkdir /usr/share/nginx/html
RUN mkdir /usr/share/nginx/html/login
RUN mkdir /usr/share/nginx/html/console
COPY console /usr/share/nginx/html/console
COPY login /usr/share/nginx/html/login
COPY index.html /usr/share/nginx/html/
COPY logo.gif /usr/share/nginx/html/
COPY signup.html /usr/share/nginx/html/
COPY signup.js /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
