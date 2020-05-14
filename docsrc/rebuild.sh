cd ../ && python setup.py install -f && cd -
rm -rf src/_generated
rm -rf build/*
make html
make github 

