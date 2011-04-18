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
            if key in self.__dict__ and len(args) < 200:
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
        
        projectfiles = self.getfilelist(".","project.yaml")
        
        try:
            assert(len(projectfiles) == 1)
        except AssertionError:
            raise ProjectLoadFatalError, "Project must have *exactly* one file *.project.yaml in the root folder!"
        filename = os.path.join(self.path, projectfiles[0])
        print "project filename:" , filename
        self.project = self.loadfile(filename)
        self.project.load(self,self.path,".")
        return self.project

    def getfilelist(self, folder, ext):
        if folder not in self.filetree:
            print "WARN: folder %s does not exist." % repr(folder)
            return []
            
        return [ fname for fname in self.filetree[folder] if fname.endswith(".%s" % ext) ]
    
    def loadfile(self,name):
        ret = yaml.load(open(name).read())
        ret.yaml_afterload()
        return ret

class LlampexBaseFile(BaseLlampexObject):
    tagorder = ["code","name","version","icon","shortcut","weight"]
    childtype = None
    
    def require_attribute(self, key):
        if not hasattr(self,key): raise AttributeError, "%s attribute not found!" % repr(key)
        
    def default_attribute(self, key, val):
        if not hasattr(self,key): setattr(self,key,val)
        
    def filedir(self, x):
        return os.path.join(self.filepath,x)
        
    def contentdir(self, x):
        return os.path.join(self.fullpath,x)
        
    def yaml_afterload(self):
        super(LlampexBaseFile,self).yaml_afterload()
        self.require_attribute("code")
        self.require_attribute("name")
        self.default_attribute("version", None)
        self.default_attribute("icon", None)
        self.default_attribute("shortcut", None)
        self.default_attribute("weight", "zzz")
        self.weight = unicode(self.weight)

    def load(self,loader,root,path):
        if self.childtype is None:
            #print "Class %s has no childs" % (self.__class__.__name__)
            return
        path = os.path.normpath(path)
        self.root = root
        self.path = path
        self.loader = loader

        files = self.loader.getfilelist(self.path,"%s.yaml" % self.childtype)
        fullpath = os.path.join(self.root, self.path)
        self.fullpath = fullpath
        
        tmplist = []
        for fname in sorted(files):
            fullname = os.path.join(fullpath, fname)
            child = self.loader.loadfile(fullname)
            
            tmplist.append( (child.weight, child.code, child) )
        
        self.child_list = []
        self.child = {}
        
        if not tmplist:
            print "WARN: %s has no childs of type %s" % (self.__class__.__name__, self.childtype)
        
        for w,c,child in sorted(tmplist):
            self.child_list.append(c)
            self.child[c] = child
            child.filepath = self.fullpath
            if hasattr(child,"load"):
                child.load(loader, root, os.path.join(path,c))
        
        setattr(self,"%s" % self.childtype, self.child)
        setattr(self,"%s_list" % self.childtype, self.child_list)
        
        
        
class LlampexProject(LlampexBaseFile):
    yaml_tag = u'!LlampexProject' 
    tagorder = LlampexBaseFile.tagorder + []
    childtype = "area"

class LlampexArea(LlampexBaseFile):
    yaml_tag = u'!LlampexArea' 
    tagorder = LlampexBaseFile.tagorder + []
    childtype = "module"
    def yaml_afterload(self):
        super(LlampexArea,self).yaml_afterload()
        self.default_attribute("description","")

class LlampexModule(LlampexBaseFile):
    yaml_tag = u'!LlampexModule' 
    tagorder = LlampexBaseFile.tagorder + []
    childtype = "group"

class LlampexGroup(LlampexBaseFile):
    yaml_tag = u'!LlampexGroup' 
    tagorder = LlampexBaseFile.tagorder + []
    childtype = "action"

class LlampexAction(LlampexBaseFile):
    yaml_tag = u'!LlampexAction' 
    tagorder = LlampexBaseFile.tagorder + []
    def yaml_afterload(self):
        super(LlampexAction,self).yaml_afterload()
        self.require_attribute("table")
        self.require_attribute("record")
        self.require_attribute("master")
        self.require_attribute("description")
        
        
        