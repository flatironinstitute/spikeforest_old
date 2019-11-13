const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlWebpackRootPlugin = require('html-webpack-root-plugin');
var version = require('./package.json').version;

module.exports = [];

module.exports.push({
	// This is where our app starts.
	entry: ["babel-polyfill", './src/index.js'],
	// module is where we
	// define all the rules for how webpack will deal with things.
	module: {
		// rules takes an array, each item containing the respective rules
		rules: [
			{
				// First up, our JavaScript rules.
				test: /\.js$/,
				// Don't bother spending time transpiling your installed packages
				exclude: /node_modules/,
				// Use babel to transpile our JS.
				use: {
					loader: 'babel-loader',
					options: {
						presets: ["@babel/preset-env", "@babel/preset-react"],
						plugins: ["@babel/plugin-proposal-class-properties", "react-hot-loader/babel"]
					}
				}
			},
			{
				// CSS files
				test: /\.css$/,
				use: [
					{ loader: 'style-loader' },
					{ loader: 'css-loader' }
				],
			},
			{
				// py files
				test: /\.py$/i,
				use: {
					loader: 'raw-loader'
				}
			},
			{
				// Some image formats so you can import images
				test: /\.(png|gif|jpg|svg)$/,
				use: {
					loader: 'url-loader',
					options: {
						limit: 50000,
					},
				},
			},
		],
	},
	// Here we define explicitly the file types we intend to deal with
	resolve: {
		extensions: ['.css', '.js', '.json', '.png', '.gif', '.jpg', '.svg'],
		alias: {
            'react-dom': '@hot-loader/react-dom'
		}
	},
	// This is where we define how everything gets output.
	// dist is a common output folder, and it should be gitignored.
	output: {
		path: path.resolve(__dirname, 'dist/'),
		publicPath: '',
		// You can do fun things here like use the [hash] keyword to generate unique
		// filenames, but for this purpose mountainbrowser.js is fine. This file and path will
		// be what you put in package.json's "main" field
		filename: 'mountainbrowser.js',
		// This field determines how things are importable when installed from other
		// sources. UMD may not be correct now and there is an open issue to fix this,
		// but until then, more reading can be found here:
		// https://webpack.js.org/configuration/output/#output-librarytarget
		libraryTarget: 'umd',
	},
	plugins: [
		new HtmlWebpackPlugin({
			template: 'src/index_template.html',
			title: 'MountainBrowser'
		}),
		new HtmlWebpackRootPlugin()
	],
	optimization: {
		// Create a separate file for vendor modules
		splitChunks: {
			cacheGroups: {
				commons: {
					test: /[\\/]node_modules[\\/]/,
					name: 'vendors',
					chunks: 'all'
				}
			}
		}
	},
	devServer: {
		contentBase: 'dist',
		port: 5050
	}
});

/*
/////////////////////////////////////////////////
// JUPYTER

var jupyter_rules = [
    {
        // First up, our JavaScript rules.
        test: /\.js$/,
        // Don't bother spending time transpiling your installed packages
        exclude: /node_modules/,
        // Use babel to transpile our JS.
        use: {
            loader: 'babel-loader',
            options: {
                presets: ["@babel/preset-env", "@babel/preset-react"],
                plugins: ["@babel/plugin-proposal-class-properties"]
            }
        }
    },
    {
        // CSS files
        test: /\.css$/,
        use: [
            { loader: 'style-loader' },
            { loader: 'css-loader' }
        ],
    },
    {
        // py files
        test: /\.py$/i,
        use: {
            loader: 'raw-loader'
        }
    },
    {
        // Some image formats so you can import images
        test: /\.(png|gif|jpg|svg)$/,
        use: {
            loader: 'url-loader',
            options: {
                limit: 50000,
            },
        },
    },
]


module.exports.push(
    {// Notebook extension
     //
     // This bundle only contains the part of the JavaScript that is run on
     // load of the notebook. This section generally only performs
     // some configuration for requirejs, and provides the legacy
     // "load_ipython_extension" function which is required for any notebook
     // extension.
     //
        entry: './jupyter/js/lib/extension.js',
        output: {
            filename: 'extension.js',
            path: path.resolve(__dirname, 'jupyter', 'mountainbrowser', 'static'),
            libraryTarget: 'amd'
        }
	}
);

module.exports.push(
    {// Bundle for the notebook containing the custom widget views and models
     //
     // This bundle contains the implementation for the custom widget views and
     // custom widget.
     // It must be an amd module
     //
        entry: './jupyter/js/lib/index.js',
        output: {
            filename: 'index.js',
            path: path.resolve(__dirname, 'jupyter', 'mountainbrowser', 'static'),
            libraryTarget: 'amd'
        },
        devtool: 'source-map',
        module: {
            rules: jupyter_rules
        },
        externals: ['@jupyter-widgets/base']
	}
);

module.exports.push(
    {// Embeddable bundle
     //
     // This bundle is generally almost identical to the notebook bundle
     // containing the custom widget views and models.
     //
     // The only difference is in the configuration of the webpack public path
     // for the static assets.
     //
     // It will be automatically distributed by unpkg to work with the static
     // widget embedder.
     //
     // The target bundle is always `dist/index.js`, which is the path required
     // by the custom widget embedder.
     //
        entry: './jupyter/js/lib/embed.js',
        output: {
            filename: 'index.js',
            path: path.resolve(__dirname, 'jupyter', 'dist'),
            libraryTarget: 'amd',
            publicPath: 'https://unpkg.com/mountainbrowser@' + version + '/dist/'
        },
        devtool: 'source-map',
        module: {
            rules: jupyter_rules
        },
        externals: ['@jupyter-widgets/base']
    }
);
*/
