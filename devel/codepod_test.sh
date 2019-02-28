#!/bin/bash
set -ex

PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider
