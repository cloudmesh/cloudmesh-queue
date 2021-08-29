import os
from cloudmesh.queue.jobqueue import Job
from cloudmesh.queue.jobqueue import Host

class RemoteSSH:

    def __init__(self, user, host, directory="~/."):
        self.user = user
        self.host = host
        self.name = None
        self.directory = directory
        self.pid = None
        self.status = "defined"
        self.uuid = None

    def run(self, name, command, directory="~/."):
        # run job remotely with ssh in nohup
        # redirect pid to file in homedir
        # copy pid and put in db
        # develop output parser to check for job states
        # such as # cm-status: running, deleted, done, defined
        self.name = name
        self.pid = "TBD"
        self.status = "running"
        self.command = command
        self.directory = directory

        job = Job(directory=directory,command=command, name=name)

        job.generate()

        print(job)


        #_command = (
        #        f"ssh {self.user}@{self.host} "
        #        f"\"cd {self.directory}; "
        ##        f"sh -c 'echo PID=$$' > {name}.log; "
        #        f"exec {self.command}\""
        #)
        #print (_command)
        # r = os.system(_command)
        #print ("R:", r)

    @classmethod
    def status(self, uuid=None, name=None):
        if uuid:
            return "TBD"
        elif name:
            return "TBD"
        raise ValueError("can not find job")


