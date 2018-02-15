var path = require("path");
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');


module.exports = {
  context: __dirname,
  entry: {
    index: './assets/js/index',
    bootstrap: 'bootstrap-loader',
  },
  output: {
      path: path.resolve('./assets/bundles/'),
      filename: "[name]-[hash].js",
      publicPath: '/static/bundles/',
  },
  module: {
    rules: [
      // we pass the output from babel loader to react-hot loader

      { test: /\.scss$/, use: ['style-loader', 'css-loader', 'postcss-loader', 'sass-loader'] },
      { test: /\.(jpe?g|png|gif)$/i, use: [ "file-loader" ] },
      { test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/, use: "url-loader?limit=10000&mimetype=application/font-woff", },
      { test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/, use: 'file-loader', },
      { test: /bootstrap-sass\/assets\/javascripts\//, use: 'imports-loader?jQuery=jquery' },
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              presets: ['env', 'react'],
              plugins: [
                // 'transform-jsx',
                "transform-object-rest-spread"
              ]
            }
          }
        ],
      },
      {
        test: /\.css$/,
        use: [
          { loader: "style-loader" },
          { loader: "css-loader" }
        ]
      }
    ],
  },
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],

  externals: {
    "jquery": "jQuery",
  },

  resolve: {
    modules: [
      path.join(__dirname, "assets/js"),
      "node_modules"
    ],
    // enforceExtension: false,
    extensions: ['*', '.js', '.jsx']
  },
}
