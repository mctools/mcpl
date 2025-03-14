#!/usr/bin/env bash
set -e
set -u
export REPOROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

function pymcpltool {
    python3 "${REPOROOT}/mcpl_python/src/mcpl/mcpl.py" "$@"
}
function md5sum {
    python3 -c 'import hashlib,sys,pathlib; print(hashlib.md5(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$1"
}


PYTHONIOENCODING=
for pyio in none ascii utf8; do
    if [ "x$pyio" == "xnone" ]; then
        unset PYTHONIOENCODING
    else
        export PYTHONIOENCODING="$pyio"
    fi
    for loc in donothing C; do
        log=output_pyio_${pyio}_lang_${loc}.txt
        echo "======================================>"
        echo "====> RUNNING TESTS WITH PYIO: $pyio LC/LANG: $loc (output goes to $log)"
        echo "======================================>"
        if [ "x$loc" != "xdonothing" ]; then
            export LC_ALL=$loc
            export LC_CTYPE=$loc
            export LANG=$loc
            export LANGUAGE=$loc
        fi
        cmd="pymcpltool ${REPOROOT}/tests/data/ref/reffile_encodings.mcpl.gz" > $log
        $cmd >> $log
        $cmd -nl3 >> $log
        for bk in asciidata asciidata_empty utf8data binarydata 'utf8bløbkey' `echo -ne "notutf8key_\xff\xfe_"`; do
            echo "=====> dumping blob key \"${bk}\"" >> $log
            $cmd -b"${bk}" >> $log
            echo >> $log
            echo -n md5sum: >> $log



            $cmd -b"${bk}" > tmpfile.txt
            md5sum tmpfile.txt >> $log
        done
        if [ "x$loc" != "xC" -a "x$pyio" != "xnone" ]; then
            diff -a output_pyio_none_lang_C.txt $log
        fi
    done
done

echo "======================================>"
echo "====> All tests produced identical output, reproduced here:"
echo "======================================>"
cat output_pyio_none_lang_C.txt
