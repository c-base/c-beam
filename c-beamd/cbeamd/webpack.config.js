var path = require("path");
var fs = require("fs");
var webpack = require('webpack');

// webpack-bundle-tracker 0.0.5 writes the pre-1.0 stats format: chunks as a
// list of objects, and no assets map. django-webpack-loader 3.2.3 expects the
// current one — an assets map, with chunks as a list of asset names — and
// fails on the old shape with "expected string or bytes-like object, got
// 'dict'". the tracker cannot be upgraded without moving off webpack 1, so
// the stats file is written here instead.
function BundleTracker(options) {
  this.filename = options.filename;
}

BundleTracker.prototype.write = function (data) {
  fs.writeFileSync(
    path.resolve(__dirname, this.filename),
    JSON.stringify(data, null, 2)
  );
};

BundleTracker.prototype.apply = function (compiler) {
  var self = this;

  compiler.plugin('done', function (stats) {
    var json = stats.toJson({ chunkModules: false, source: false });

    if (json.errors.length) {
      self.write({ status: 'error', error: 'webpack build failed',
                   message: json.errors.join('\n') });
      return;
    }

    var assets = {};
    var chunks = {};

    Object.keys(json.assetsByChunkName).forEach(function (chunkName) {
      var files = json.assetsByChunkName[chunkName];
      if (!Array.isArray(files)) {
        files = [files];
      }
      chunks[chunkName] = files;
      files.forEach(function (file) {
        assets[file] = { name: file };
      });
    });

    self.write({ status: 'done', assets: assets, chunks: chunks });
  });

  compiler.plugin('failed', function (err) {
    self.write({ status: 'error', error: 'webpack build failed',
                 message: String(err) });
  });
};


module.exports = {
  context: __dirname,
  entry: {
    index: './assets/js/index',
  },
  output: {
      path: path.resolve('./assets/bundles/'),
      filename: "[name]-[hash].js",
  },

  externals: {
    // require("jquery") is external and available
    //  on the global var jQuery
    //"react": "React",
    //"react-dom": "ReactDOM",
    "jquery": "jQuery",
    //"marked": "Marked",
  },
  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
  ],

  module: {
    loaders: [
      // we pass the output from babel loader to react-hot loader
      { test: /\.(es6|jsx?)$/, exclude: /node_modules/, loaders: ['babel'], },
    ],
  },

  resolve: {
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.jsx', '.es6', '.styl']
  },
}
