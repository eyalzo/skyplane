# Skyplane Documentation

Make sure you're in the project's root, and then run the following to install the packages for the documentation: 
```
pip install -r docs/requirements.txt
```

Run `cd docs/` to make sure you're in the documentation directory. Then, build the docs with: 
```
sphinx-autobuild -b html -d build/doctrees . build/html
```
which will output a localhost port where you can view the docs. 
