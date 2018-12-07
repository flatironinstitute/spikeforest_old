rm -rf build/ dist/ mlprocessors.egg-info/
python3 setup.py sdist bdist_wheel
twine upload dist/*
