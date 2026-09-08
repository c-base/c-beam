var path = require("path");
var BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  context: __dirname,
  mode: 'production',
  entry: {
    index: './assets/js/index',
  },
  output: {
      path: path.resolve(__dirname, './assets/bundles/'),
      filename: "[name]-[contenthash].js",
      // django-webpack-loader builds the url from BUNDLE_DIR_NAME when the
      // stats file carries no usable publicPath, which keeps STATIC_URL in
      // django's hands rather than hardcoding it here.
      publicPath: '',
  },

  externals: {
    // require("jquery") is external and available
    //  on the global var jQuery
    "jquery": "jQuery",
  },

  plugins: [
    new BundleTracker({path: __dirname, filename: 'webpack-stats.json'}),
  ],

  module: {
    rules: [
      { test: /\.(jsx?)$/, exclude: /node_modules/, use: 'babel-loader' },
    ],
  },

  resolve: {
    extensions: ['.js', '.jsx']
  },
}
