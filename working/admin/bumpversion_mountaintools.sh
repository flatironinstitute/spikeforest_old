#!/bin/bash

cd `dirname "$0"`/../../mountaintools

if output=$(git status --porcelain) && [ -z "$output" ]; then
  if [ -z "$1" ]; then
    echo "You must supply an option, e.g., patch, minor, major"
    exit 0
  fi
  if [ "$2" == "go" ]; then
    bumpversion $1 --verbose
    echo "Now you should push via 'git push && git push --tags' and replace the explicit version in all the docs."
  else
    bumpversion $1 --dry-run --verbose
    echo "That was a dry run. If it looks okay, then add the 'go' argument"
  fi
else 
  echo "Working directory is not clean:"
  echo "$output"
fi