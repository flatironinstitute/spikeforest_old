rm -rf build/ dist/ ml_ms4alg.egg-info/
python3 setup.py sdist bdist_wheel
twine upload dist/*
