import frontmatter

def load_study_set_from_md(fname):
    fm = frontmatter.load(fname).to_dict()
    if 'content' in fm:
        description = fm['content']
        del fm['content']
    else:
        description = ''
    study_set_name = fm['label']
    return dict(
        name=study_set_name,
        info=fm,
        description=description
    )