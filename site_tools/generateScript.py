import os, pdb, optparse, datetime, re
import SCons.Action
import SCons.Builder
from SCons.Script import AddOption, GetOption
import SomeUtils

def generateWSHScript(scriptFile, env, wrapper):
    scriptFile.write("' Autogenerated by SCons; do not edit!\n")
    scriptFile.write('set shell = CreateObject("WScript.Shell")\n')
    scriptFile.write('set env = shell.Environment("Process")\n')
    if wrapper > 0:
        scriptFile.write('INST_DIR = WScript.ScriptFullName\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('INST_DIR = Left(INST_DIR,InStrRev(INST_DIR,"\\")-1)\n')
        scriptFile.write('env("INST_DIR")=INST_DIR\n')
    scriptFile.write('COAST_ROOT = env.item("COAST_ROOT")\n')
    scriptFile.write('If COAST_ROOT = "" Then\n')
    scriptFile.write('  WScript.Echo("What is the location of the External libraries?")\n')
    scriptFile.write('  WScript.Echo("If you set %COAST_ROOT% to this location this script will no longer ask")\n')
    scriptFile.write('  COAST_ROOT = WScript.StdIn.ReadLine()\n')
    scriptFile.write('  env("COAST_ROOT")=COAST_ROOT\n')
    scriptFile.write('End If\n')
    scriptFile.write('env("PATH") = env.Item("PATH") & ";" & INST_DIR & "\\' + str(os.path.join(env['LIBDIR'], env['VARIANTDIR'])) + '"\n')
    scriptFile.write('If COAST_ROOT = "" or INST_DIR = "" Then\n')
    scriptFile.write('  WScript.Echo("COAST_ROOT not set or unable to determine installation directory")\n')
    scriptFile.write('  WScript.Quit(1)\n')
    scriptFile.write('End If\n')
    scriptFile.write('env("PATH") = env.Item("PATH") ')
    scriptFile.write('\n')
    scriptFile.write('set filesystemObject = CreateObject("Scripting.FileSystemObject")\n')
    scriptFile.write('For i=0 to WScript.Arguments.Count-1\n')
    scriptFile.write('  arguments = arguments & WScript.Arguments.Item(i) & " "\n')
    scriptFile.write('Next\n')
    scriptFile.write('env("PYTHONPATH") = INST_DIR & "\\python" & env("PYTHONPATH")\n')
    return

def generateShellScript(scriptFile, env, binpath):
    scriptText = """#!/bin/sh
#-----------------------------------------------------------------------------------------------------
# Copyright (c) """ + datetime.date.today().strftime('%Y') + """, Peter Sommerlad and IFS Institute for Software at HSR Rapperswil, Switzerland
# All rights reserved.
#
# This library/application is free software; you can redistribute and/or modify it under the terms of
# the license that is included with this library/application in the file license.txt.
#-----------------------------------------------------------------------------------------------------
# Autogenerated by SConsider; do not edit!

MYNAME=`basename $0`
SCRIPTPATH=`dirname $0`
SCRIPTPATH=`cd $SCRIPTPATH 2>/dev/null && pwd -P`
STARTPATH=`pwd -P`

LIBDIR=\""""+env['LIBDIR']+"""\"
BINDIR=\""""+env['BINDIR']+"""\"
SCRIPTDIR=\""""+env['SCRIPTDIR']+"""\"
CONFIGDIR=\""""+env['CONFIGDIR']+"""\"
VARIANTDIR=\""""+env['VARIANTDIR']+"""\"
BASEOUTDIR=\""""+env['BASEOUTDIR'].abspath+"""\"
RELTARGETDIR=\""""+env['RELTARGETDIR']+"""\"
BINARYNAME=\""""+os.path.basename(binpath)+"""\"

doChangeDir=1
doDebug=0
doTrace=0

showhelp()
{
    echo ''
    echo 'usage: '$MYNAME' [options]'
    echo 'where options are:'
    echo ' -d            : run under debugger control (gdb)'
    echo ' -S            : do not change directory before executing target, eg. Stay in current directory'
    echo ' -v            : verbose mode'
    echo .
    exit 3;
}

while getopts ":dSv-" opt
do
    case $opt in
        :)
            echo "ERROR: -$OPTARG parameter missing, exiting!";
            showhelp;
        ;;
        d)
            doDebug=1;
        ;;
        S)
            doChangeDir=0;
        ;;
        v)
            doTrace=1;
        ;;
        -)
            break;
        ;;
        \?)
            showhelp;
        ;;
    esac
done

shift `expr $OPTIND - 1`

# find base directory for a given path
# param $1 path to start from
# param $2 is the path segment to search for
# param $3 variable to store resulting base path into
searchBaseDirUp()
{
    start_dir=${1};
    searchSegment=${2};
    ret_var=${3};
    basePath=`cd $start_dir &&
        while [ ! -d ${searchSegment} ] && [ \`pwd\` != / ]; do
            cd .. 2>/dev/null;
        done;
        pwd -P
    `;
    test -d ${basePath} || basePath="";
    eval ${ret_var}="$basePath";
}

# find the base directory
LIBDIR_BASE=${STARTPATH}
searchBaseDirUp "${SCRIPTPATH}" "${LIBDIR}" LIBDIR_BASE

test -n "${LIBDIR_BASE}" || ( echo "Base directory not found containing [$LIBDIR], exiting."; exit 1 )

ABS_LIBDIR=${LIBDIR_BASE}/${LIBDIR}
test -d ${ABS_LIBDIR}/${VARIANTDIR} && ABS_LIBDIR=${ABS_LIBDIR}/$VARIANTDIR

LD_LIBRARY_PATH=${ABS_LIBDIR}:$LD_LIBRARY_PATH
export LD_LIBRARY_PATH

BINDIR_BASE=${STARTPATH}
searchBaseDirUp "${SCRIPTPATH}" "${BINDIR}" BINDIR_BASE

test -n "${BINDIR_BASE}" || ( echo "Base directory not found containing [$BINDIR], exiting."; exit 1 )

ABS_BINDIR=${BINDIR_BASE}/${BINDIR}
test -d ${ABS_BINDIR}/${VARIANTDIR} && ABS_BINDIR=${ABS_BINDIR}/$VARIANTDIR

# param $1 is the name of the generated file
# param $2 arguments passed to the debugged progam, do not forget to quote them!
# param $3 run executable within script or not, default 1, set to 0 to execute it manually
#
generateGdbCommandFile()
{
    outputfile=${1};
    locsrvopts="${2}";
    locRunAsServer=${3:-1};
    # <<-EOF ignore tabs, nice for formatting heredocs
cat > ${outputfile} <<-EOF
    handle SIGSTOP nostop nopass
    handle SIGLWP  nostop pass
    handle SIGTERM nostop pass
#    handle SIGINT  nostop pass
    set environment PATH=${PATH}
#    set environment COAST_ROOT=${COAST_ROOT}
#    set environment COAST_PATH=${COAST_PATH}
    set environment LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
#    set environment LOGDIR=${LOGDIR}
#    set environment PID_FILE=${PID_FILE}
    set auto-solib-add 1
    file ${WDS_BIN}
    set args "${locsrvopts}"
EOF
    if [ $locRunAsServer -eq 1 ]; then
cat >> ${outputfile} <<-EOF
    run
    where
    continue
    shell rm ${outputfile}
    quit
EOF
    fi;
}

CMD=${ABS_BINDIR}/${BINARYNAME}
test -x ${CMD} || ( echo "binary [${CMD}] is not executable, aborting!"; exit 1 )

test ${doChangeDir} -eq 1 -a -d ${BINDIR_BASE} && cd ${BINDIR_BASE}

test ${doTrace} -eq 1 && ( cat <<EOF
Executing command [${CMD}]
`test -z "$@" || echo " with arguments   [$@]"`
 in directory     [`pwd`]
EOF
)

if [ ${doDebug:-0} -eq 1 ]; then
    WDS_BIN=$CMD
    cfg_gdbcommands="/tmp/`basename $0`_$$";
    generateGdbCommandFile ${cfg_gdbcommands} "$@" 0
    test ${doTrace} -eq 1 && echo "Generated gdb command file:"
    test ${doTrace} -eq 1 && cat ${cfg_gdbcommands}
    gdb --command ${cfg_gdbcommands}
else
    $CMD "$@"
fi

exit $?
"""
    scriptFile.write(scriptText)

def generatePosixScript(target, source, env):
    for t, s in zip(target, source):
        scriptFile = open(str(t), 'w')
        generateShellScript(scriptFile, env, s.get_path())
        scriptFile.close()
    return 0

def generateWindowsScript(target, source, env):
    for t, s in zip(target, source):
        scriptFile = open(str(t), 'w')
        generateWSHScript(scriptFile, env, 1)
        scriptFile.write('shell.Run "cmd.exe /k """ & INST_DIR & "\\' + str(s) + '"" " & arguments, 1, true')
        scriptFile.close()

def generateScriptEmitter(target, source, env):
    target = []
    for src in source:
        if env['PLATFORM'] != 'win32':
            target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['SCRIPTDIR']).Dir(env['VARIANTDIR']).File(os.path.basename(src.abspath)))
        else:
            target.append(env['BASEOUTDIR'].Dir(env['RELTARGETDIR']).Dir(env['SCRIPTDIR']).Dir(env['VARIANTDIR']).File(os.path.splitext(os.path.basename(src.abspath))[0] + ".vbs"))
    return (target, source)

def generateWrapperScript(env, target):
    return env.Depends(env.GenerateScriptBuilder(target), SomeUtils.getPyFilename(__file__))

def generate(env):
    if env['PLATFORM'] != 'win32':
        GenerateScriptAction = SCons.Action.Action(generatePosixScript, "Creating wrapper script for '$TARGET'")
        GenerateScriptBuilder = SCons.Builder.Builder(action=[GenerateScriptAction, SCons.Defaults.Chmod('$TARGET', 0755)],
                                                      emitter=generateScriptEmitter,
                                                      single_source=1)
    else:
        GenerateScriptAction = SCons.Action.Action(generateWindowsScript, "Creating wrapper script fpr '$TARGET'")
        GenerateScriptBuilder = SCons.Builder.Builder(action=[GenerateScriptAction], emitter=generateScriptEmitter, single_source=1)

    env.Append(BUILDERS={ 'GenerateScriptBuilder' : GenerateScriptBuilder })
    env.AddMethod(generateWrapperScript, "GenerateWrapperScript")

def exists(env):
    return 1;
