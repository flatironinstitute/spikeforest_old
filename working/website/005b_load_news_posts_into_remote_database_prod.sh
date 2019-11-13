#!/bin/bash
set -e

./make_news_posts.py
./load_news_posts_into_remote_database_prod.sh news_posts
