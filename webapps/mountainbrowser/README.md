# MountainBrowser

MountainBrowser is a static HTML application built using ReactJS.

## Normal installation

First install the node modules

```
yarn install
```

The following will create distribution files in the dist/ directory. It allows browsing of sha1dir:// directories and interfaces with kachery databases and other MountainTools components.

```
yarn build
```

You can then either open dist/index.html in a browser, or run a server on port 6060 via:

```
PORT=6060 yarn start
```

## Development installation

First install the node modules

```
yarn install
```

The following command will start a hot-module-loading development server and open a browser pointing to the proper local port.

```
yarn dev

# then in a separate terminal:
./open_as_chrome_app.sh
```
