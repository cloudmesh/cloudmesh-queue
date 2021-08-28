class RemoteSSH:

    def __init__(self, name, user, host, command, directory):
        self.user = user
        self.host = host
        self.command = command
        self.name = name
        self.directory = directory
        self.pid = None
        self.status = "defined"
        self.uuid = None

    def run(self):
        pass
        # run job remotely with ssh in nohup
        # redirect pid to file in homedir
        # copy pid and put in db
        # develop output parser to check for job states
        # such as # cm-status: running, deleted, done, defined
        self.pid = "TBD"
        self.status = "running"

    @classmethod
    def status(self, uuid=None, name=None):
        if uuid:
            return "TBD"
        elif name:
            return "TBD"
        raise ValueError("can not find job")


