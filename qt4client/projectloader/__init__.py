# encoding: UTF-8
import os.path, os
import yaml
import re

class BaseLlampexObject(yaml.YAMLObject):
    yaml_tag = u'!LlampexBASE' 
    tagorder = []
    taghidden = []
    taghidefalse = True
    def __init__(self,*args,**kwargs):
        super(BaseLlampexObject,self).__init__()
        
    def __getstate__(self):
        listpairs = []
        knownkeys = self.__dict__.keys()[:]
        for key in self.tagorder:
            if key in knownkeys:
                if not self.taghidefalse or self.__dict__[key]:
                    listpairs.append( (key,self.__dict__[key]) )
                knownkeys.remove(key)
        knownkeys.sort()
        for key in knownkeys:
            if key[0] == '_': continue
            if key in self.taghidden: continue
            if not self.taghidefalse or self.__dict__[key]:
                listpairs.append( (key,self.__dict__[key]) )
        
        return listpairs
    def __repr__(self):
        args = ""
        for key in self.tagorder:
            if key in self.__dict__ and len(args) < 80:
                value = self.__dict__[key]
                if value and len(repr(value)) < 32:
                    args+=" " + key + "=" + repr(value)
            
        return "<%s%s>" % (self.__class__.__name__,args)
    
    def yaml_afterload(self):
        pass
    

class ProjectLoadFatalError(Exception):
    """
        Error raised whenever the project fails to load.
    """

class ProjectLoader(object):
    def __init__(self, path, files):
        self.path = path
        self.files = files
        self.filetree = {}
        
        self.project = None
    
    def load(self):
        print "Loading project at" , self.path
        
        for filepath in self.files:
            dirname, filename = os.path.split(filepath)
            if dirname not in self.filetree:
                self.filetree[dirname] = []
            self.filetree[dirname].append(filename)
        """    
        for dirname in sorted(self.filetree.keys()):
            print dirname, " *** "
            print repr(list(sorted(self.filetree[dirname])))
            print
        """ 
        
        projectfiles = [ fname for fname in self.filetree["."] if fname.endswith(".project.yaml") ]
        areafiles = [ fname for fname in self.filetree["."] if fname.endswith(".area.yaml") ]
        
        try:
            assert(len(projectfiles) == 1)
        except AssertionError:
            raise ProjectLoadFatalError, "Project must have *exactly* one file *.project.yaml in the root folder!"
            
        try:
            assert(len(areafiles) >= 1)
        except AssertionError:
            raise ProjectLoadFatalError, "Project must have *at least* one area (one file *.area.yaml in the root folder!)"
        
        filename = os.path.join(self.path, projectfiles[0])
        print "project filename:" , filename
        self.project = self.loadfile(filename)
        print "project:",  repr(self.project)
        print self.project.code, self.project.version
    
    def loadfile(self,name):
        ret = yaml.load(open(name).read())
        ret.yaml_afterload()
        return ret

class LlampexBaseFile(BaseLlampexObject):
    tagorder = ["code","name","version","icon","weight"]
    def yaml_afterload(self):
        super(LlampexBaseFile,self).yaml_afterload()
        if not hasattr(self,"code"): raise AttributeError, "code attribute not found!"
        if not hasattr(self,"name"): raise AttributeError, "name attribute not found!"
        if not hasattr(self,"version"): self.version = None
        if not hasattr(self,"icon"): self.icon = None
        if not hasattr(self,"weight"): self.weight = "zz"
        
        
    
class LlampexProject(LlampexBaseFile):
    yaml_tag = u'!LlampexProject' 
    tagorder = LlampexBaseFile.tagorder + []

    