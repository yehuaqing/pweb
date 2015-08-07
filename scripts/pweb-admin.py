#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import pweb

def copyFiles(sourceDir, targetDir):
    for f in os.listdir(sourceDir):
        sourceF = os.path.join(sourceDir, f)
        targetF = os.path.join(targetDir, f)

        if os.path.isfile(sourceF):
            #make targetDir
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            #skip pyc file
            if os.path.splitext(sourceF)[1].lower()=='.pyc':
                continue

            #copy file
            open(targetF, "wb").write(open(sourceF, "rb").read())

        if os.path.isdir(sourceF):
            copyFiles(sourceF, targetF)
    return True

def main(argv):
    sourceDir = os.path.join(pweb.__path__[0], "examples")

    if len(argv) not in [1, 2]:
        print "useage: pweb-admin.py <projectname> <createonpath>"
        return

    if len(argv) == 1:
        prjname = argv[0].strip()
        prjpath = os.path.abspath(os.curdir)

    if len(argv) == 2:
        prjname, prjpath = [x.strip() for x in argv]

    targetDir = os.path.join(prjpath, prjname)
    if os.path.isdir(targetDir):
        print "Project Path %s is Exists. Can't Create New."% prjpath
        return

    ret = copyFiles(sourceDir, targetDir)
    if ret:
        print "Create NewPwebProject: %s on %s Success!"% (prjname, prjpath)
    else:
        print "Create NewPwebProject: %s on %s failed."% (prjname, prjpath)

if __name__=="__main__":
    main(sys.argv[1:])

