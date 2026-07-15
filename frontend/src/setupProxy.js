// react-scripts 5 bundles http-proxy-middleware v2, which replaced the default
// `proxy(context, options)` export with a named `createProxyMiddleware(options)`
// and expects the path to be passed to app.use().
const { createProxyMiddleware } = require('http-proxy-middleware');

let proxy_location = '';

if (process.env.DJANGO_PROXY_HOST && process.env.DJANGO_PROXY_PORT){
  proxy_location=process.env.DJANGO_PROXY_HOST + ":" + process.env.DJANGO_PROXY_PORT;
}
else{
  proxy_location='localhost:8000';
}

module.exports = function(app) {
  app.use('/api', createProxyMiddleware({ target: 'http://' + proxy_location }));
  app.use('/tunnelws', createProxyMiddleware({ target: 'ws://' + proxy_location, ws: true }));
  app.use('/admin', createProxyMiddleware({ target: 'http://' + proxy_location }));
  app.use('/accounts', createProxyMiddleware({ target: 'http://' + proxy_location }));
  app.use('/staticfiles', createProxyMiddleware({ target: 'http://' + proxy_location }));
};
