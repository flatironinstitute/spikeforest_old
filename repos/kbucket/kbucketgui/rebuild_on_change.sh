#!/bin/bash
while inotifywait -e modify -e delete -r $PWD; do
  npm run webpack
done

