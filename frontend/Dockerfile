FROM node:20-alpine

ADD package.json /frontend/
ADD package-lock.json /frontend/

WORKDIR /frontend
RUN npm install

ENV REACT_APP_VERSION=dev-in-docker

CMD ["npm","run","start"]


