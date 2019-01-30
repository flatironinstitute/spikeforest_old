#!/bin/bash
set -ex

pip install -r requirements.txt
python setup.py develop
pip install jupyterlab

#if [ -d /home/theiapod ]; then
#    echo "test"
#    for filename in /home/theiapod/{*,.??*}; do
#        echo "testing --- $filename"
#        if [ -e "$filename" ]; then # in case no such file exists
#            fname=$(basename $filename)
#            ln -s /home/theiapod/$fname ~/$fname
#        fi
#    done
#fi

#if [ -f /home_data/.gitconfig ]; then
#    ln -s /home_data/.gitconfig ~/.gitconfig
#fi
