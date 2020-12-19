# !/usr/bin/env python

from cloudmesh.common.Shell import Shell
from cloudmesh.common.util import readfile
from cloudmesh.common.util import writefile
import textwrap

manual = 0
man = Shell.run("cms job help")
# remove timer
man = man.split("\nTimer: ")[0]

readme = readfile("README.md")

parts = readme.split("<!-- MANUAL -->")

print (parts[0])
print ("<!-- MANUAL -->")
print ("```bash")
print (textwrap.dedent("\n".join(man.splitlines()[7:])))
print ("```")
print ("<!-- MANUAL -->")
print (parts[1])



