# !/usr/bin/env python

from cloudmesh.common.Shell import Shell
from cloudmesh.common.util import readfile
from cloudmesh.common.util import writefile

manual = False
man = Shell.run("cms job help")
for line in man.splitlines():
   if "<!-- MANUAL -->" in line:
        manual = not manual
   if manual:
      print (man)
   else:
       pass
   if not manual:
       print(line)
