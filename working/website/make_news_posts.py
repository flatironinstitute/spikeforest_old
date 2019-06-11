#!/usr/bin/env python

import os
import shutil
import json
import frontmatter


def main():
    if os.path.exists('news_posts'):
        shutil.rmtree('news_posts')
    os.mkdir('news_posts')

    newspath = '../../docs/news'
    news_posts = []
    for fname in os.listdir(newspath):
        if fname.endswith('.md'):
            fm = frontmatter.load(newspath + '/' + fname).to_dict()
        news_posts.append(dict(
            title=fm['title'],
            date=fm['date'].isoformat(),
            author=fm['author'],
            markdown=fm['content']
        ))

    out_fname = 'news_posts/NewsPosts.json'
    print('Writing to {}'.format(out_fname))
    with open(out_fname, 'w') as f:
        json.dump(news_posts, f)
    print('Done.')

if __name__ == "__main__":
    main()
