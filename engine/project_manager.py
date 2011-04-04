
class ProjectManager(object):
    available_projects = []
    def __init__(self, prj):
        self.data = prj
        self.load()
        self.available_projects.append(self)
        
    def load(self):
        print "Loading . . . " , self.data
        
    