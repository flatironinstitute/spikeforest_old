#!/bin/bash
set -e

./make_news_posts.py
./load_news_posts_into_local_database.sh news_posts