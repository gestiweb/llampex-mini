# encoding: UTF-8
import os.path, os
import yaml
import re, traceback

"""
    Handling paths:
    
    All paths are relative from the YAML file that were read from. For example:
    
    icon: icons/customer.png
    
    is a file inside a subfolder relative to the yaml filepath.
    You can also specify the ".." directory to refer parent folders:
    
    icon: ../../customer.png
    
    If you want to refer to the root of project you can use either absolute paths
    or :project:/ paths. 
    
    icon: /generic/icons/edit.png
    script: :project:/generic/icons/edit.png
    
    You cannot exit out of project path by using ../ or :project: aliases.
    
    Also, you have other aliases as well depending on it is placed your yaml 
    file (or when it is loaded).
    
    :project:/ -> project root
    :area:/ -> area content folder
    :module:/ -> module content folder
    :group:/ -> group content folder
    
    :area: -> area yaml file folder
    :module: -> module yaml file folder
    :group: -> group yaml file folder
    :action: -> action yaml file folder
    
    Some of them should point to the same place. 
    The recommended format is :folder:/
    
    
"""

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
        for tname, tobj in self.project.table_index.iteritems():
            table = tobj[0]
            table.action_index = []
            
        for aname, aobj in self.project.action_index.iteritems():
            action = aobj[0]
            table = self.project.table_index[action.table]
            table.action_index.append(action)
            
        return self.project

    def getfilelist(self, folder, ext):
        if folder not in self.filetree:
            print "WARN: folder %s does not exist." % repr(folder)
            return []
            
        return [ fname for fname in self.filetree[folder] if fname.endswith(".%s" % ext) ]
    
    def loadfile(self,name):
        ret = yaml.load(open(name).read())
        ret.yaml_afterload()
        try: ret.llampexProjectFile_afterLoad(self)
        except AttributeError, e: print "ERROR Loading project afterload in ", ret
        return ret

class LlampexBaseFile(BaseLlampexObject):
    tagorder = ["code","name","version","icon","shortcut","weight"]
    childtype = None
    filetype = None
    childrensubfolder = {}
    
    def __init__(self,*args,**kwargs):
        super(LlampexBaseFile,self).__init__()
        self.dictpath = {}
        
    def require_attribute(self, key):
        if not hasattr(self,key): raise AttributeError, "%s attribute not found!" % repr(key)
        
    def default_attribute(self, key, val):
        if not hasattr(self,key): setattr(self,key,val)
        
    def filedir(self, fname):
        x = fname
        if os.path.isabs(x): x = ":project:" + x
        ftype = None
        if x[0] == ":":
            typeend = x.find(":",1)
            ftype = x[1:typeend]
            x = x[typeend+1:]
            if os.path.isabs(x):
                ftype+="/"
                x = x[1:]
                
        path = None
        if ftype is None:
            path = self.filepath
        else:
            try:
                path = self.dictpath[ftype]
            except KeyError:
                print "ERROR: Path %s invalid at %s" % (fname,self.filepath)
        
        if path is None:
            path = self.filepath
            print "WARN: rewritting path %s" % (x)
            
        ret = os.path.join(path,x)
        ret = os.path.normpath(ret)
        try:
            loaderpath = self.loader.path
            if loaderpath[-1] != "/": loaderpath+="/"
            assert(ret.startswith(loaderpath))
        except AssertionError:
            raise ValueError, "ERROR: Path %s invalid at %s. Path exits out of project!" % (fname,self.filepath)
        return ret
        
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
        self.dictpath = {}
        
    def llampexProjectFile_afterLoad(self, loader):
        project = loader.project
        ftype = self.filetype  # (project, module, area, table, action , ...)
        attrname = "%s_index" % ftype
        if not hasattr(project,attrname):
            setattr(project,attrname, {})
            
        index = getattr(project,attrname)
        
        if self.code not in index:
            index[self.code] = []
            
        index[self.code].append(self)

    def load(self,loader,root,path):
        if self.childtype is None: return
        if self.childtype is []: return
        if isinstance(self.childtype, list):
            for child in self.childtype:
                self.loadchildtype(loader,root,path,child)
        else:                
            self.loadchildtype(loader,root,path,self.childtype)
            
    def loadchildtype(self,loader,root,path,childtype):
        path = os.path.normpath(path)
        self.root = root
        self.path = path
        self.loader = loader
        if childtype in self.childrensubfolder:
            path = os.path.join(self.path,self.childrensubfolder[childtype])
        files = self.loader.getfilelist(path,"%s.yaml" % childtype)
        fullpath = os.path.join(self.root, path)
        self.fullpath = fullpath
        if self.filetype:
            self.dictpath[self.filetype+"/"] = self.fullpath
        
        tmplist = []
        for fname in sorted(files):
            fullname = os.path.join(fullpath, fname)
            try:
                child = self.loader.loadfile(fullname)
            except yaml.YAMLError, e:
                print traceback.format_exc(0)
                print "FATAL: Error scanning yaml %s:" % fullname 
                continue
            except Exception, e:
                print traceback.format_exc()
                print "PANIC: Unexpected error when loading %s:" % fullname 
                continue
            child.loader = self.loader
            child.dictpath = self.dictpath.copy()
            child.dictpath[childtype] = self.fullpath
            tmplist.append( (child.weight, child.code, child) )
        
        self.child_list = []
        self.child = {}
        
        if not tmplist:
            print "WARN: %s at %s has no childs of type %s" % (self.__class__.__name__, self.path, childtype)
        
        for w,c,child in sorted(tmplist):
            self.child_list.append(c)
            self.child[c] = child
            child.filepath = self.fullpath
            if hasattr(child,"load"):
                child.load(loader, root, os.path.join(path,c))
        
        setattr(self,"%s" % childtype, self.child)
        setattr(self,"%s_list" % childtype, self.child_list)
        
        
        
class LlampexProject(LlampexBaseFile):
    yaml_tag = u'!LlampexProject' 
    tagorder = LlampexBaseFile.tagorder + []
    filetype = "project"
    childtype = "area"
    def yaml_afterload(self):
        super(LlampexProject,self).yaml_afterload()
        #self.index = {}

class LlampexArea(LlampexBaseFile):
    yaml_tag = u'!LlampexArea' 
    tagorder = LlampexBaseFile.tagorder + []
    filetype = "area"
    childtype = "module"
    def yaml_afterload(self):
        super(LlampexArea,self).yaml_afterload()
        self.default_attribute("description","")

class LlampexModule(LlampexBaseFile):
    yaml_tag = u'!LlampexModule' 
    tagorder = LlampexBaseFile.tagorder + []
    filetype = "module"
    childtype = ["group","table"]
    childrensubfolder = { "table" : "tables" }

class LlampexGroup(LlampexBaseFile):
    yaml_tag = u'!LlampexGroup' 
    tagorder = LlampexBaseFile.tagorder + []
    filetype = "group"
    childtype = "action"

class LlampexAction(LlampexBaseFile):
    yaml_tag = u'!LlampexAction' 
    tagorder = LlampexBaseFile.tagorder + []
    filetype = "action"
    def yaml_afterload(self):
        super(LlampexAction,self).yaml_afterload()
        self.require_attribute("table")
        self.require_attribute("record")
        self.require_attribute("master")
        self.require_attribute("description")

class EmptyTemplate(object):
    pass
    
class FieldsObject(object):
    def __init__(self, parent):
        self.parent = parent
    
    def __getitem__(self, idx):
        try:
            fieldname = self.parent.fieldlist[int(idx)]
        except ValueError:
            fieldname = idx
        return self.parent.fields[fieldname]
        
        
        
class LlampexTable(LlampexBaseFile):
    yaml_tag = u'!LlampexTable' 
    tagorder = LlampexBaseFile.tagorder + []
    tableindex = {} # TODO: Mover el TableIndex al proyecto en cuestión
    # .. aquí corre el riesgo de que se mezclen las tablas de dos proyectos 
    # .. cargados a la vez o serialmente.
    filetype = "table"
    def yaml_afterload(self):
        super(LlampexTable,self).yaml_afterload()
        self.require_attribute("fields")
        self.tableindex[self.code] = self
        self.field = FieldsObject(self)
        field_ordering_list = []
        for name, field in self.fields.iteritems():
            setattr(self.field, name, field)
            field["name"] = name
            default_weight=9999
            if field.get("pk"): default_weight=0
            if field.get("unique"): default_weight=50
            if field.get("ck"): default_weight=100
            field_ordering_list.append( (field.get("weight",default_weight), name) )
        self.fieldlist = [ name for weight, name in sorted(field_ordering_list) ]
        
    @property
    def primarykey(self):
        for name, field in self.fields.iteritems():
            if field['pk']: return name
        return None
        

        
        