#!/usr/bin/env python

from mountaintools import client as mt

def main():
    path = 'sha1dir://8516cc54587e0c5ddd0709154e7f609b9b7884b4'
    mt.configDownloadFrom('spikeforest.public')
    X = mt.readDir(path)
    for study_set_name, d in X['dirs'].items():
        for study_name, d2 in d['dirs'].items():
            for recording_name, d3 in d2['dirs'].items():
                x = mt.loadObject(path=path + '/' + study_set_name + '/' + study_name + '/' + recording_name + '.runtime_info.json')
                print('{}/{}/{}\n{} sec\n'.format(study_set_name, study_name, recording_name, x['elapsed_sec']))

if __name__ == "__main__":
    main()
