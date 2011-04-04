
class ProjectManager(object):
    def __init__(self, prj):
        self.data = prj
        self.load()
        
    def load(self):
        print "Loading . . . " , self.data
        
    