#!/bin/bash

set -e

source venv/bin/activate

cd lankitapp/ui/

for f in *.ui ; do

	newname=$(sed -s 's/.ui$/.py/1' <<< $f)

	echo "$f > $newname"
	pyside2-uic $f > $newname

done

deactivate

