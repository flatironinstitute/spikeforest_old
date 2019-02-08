#!/bin/bash
set -ex

pip install --upgrade nbstripout
nbstripout --install --attributes .gitattributes
