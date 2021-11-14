const webpack = require('webpack');
const path = require('path');

module.exports = () => ({
  entry: './bin/index.js',
  output: {
    filename: 'index.js',
    path: path.resolve(__dirname, 'dist'),
  },
  plugins: [
    new webpack.EnvironmentPlugin(['DOMAIN', 'CLIENT_ID']),
    new webpack.DefinePlugin({
      'process.env.API_DOMAIN': JSON.stringify(`https://api.${process.env.DOMAIN}`),
      'process.env.LOGIN_URL': JSON.stringify(`https://${process.env.DOMAIN.split('.')[0]}.auth.us-east-1.amazoncognito.com/login?response_type=token&client_id=${process.env.CLIENT_ID}&redirect_uri=https://${process.env.DOMAIN}`),
    }),
  ],
});
