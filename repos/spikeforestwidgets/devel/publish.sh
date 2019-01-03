devel/compile.sh
rm -rf build/ dist/ mountainlab_pytools.egg-info/
python3 setup.py sdist bdist_wheel
twine upload dist/*
