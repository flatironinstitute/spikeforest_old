#!/bin/bash
set -ex 

export BATCHO_LOCAL=true
../../bin/batcho_listen test01 --parallel 10

