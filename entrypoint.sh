#!/bin/bash

set -e
set -x
set -u

cd /YeSQL
export CURRENT=$PWD
export LD_LIBRARY_PATH="$PWD/udfs/;$PWD/pypy2.7-v7.3.6-linux64/bin;$PWD/YeSQL_MonetDB/cffi_wrappers/;$PWD/monetdb_release/include/"
export PYTHONPATH="$PWD/udfs"

./monetdb_release/bin/monetdbd start flights
./monetdb_release/bin/monetdb -p 50000 start fldb
./monetdb_release/bin/mclient -d fldb -p 50000 -t performance < /test_script.sql

echo "Done!"

sleep 5

exit 0
