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



content = []

content.append(parts[0])
content.append("<!-- MANUAL -->")
content.append("```bash")
content.append(textwrap.dedent("\n".join(man.splitlines()[7:])))
content.append("```")
content.append("<!-- MANUAL -->")
content.append(parts[2])

print ("\n".join(content))



