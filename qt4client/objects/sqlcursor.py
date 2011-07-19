# encoding: UTF-8
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
from qsqlmetadatamodel import QSqlMetadataModel
import qsqlrpcdriver.qtdriver as qtdriver

"""
    ####### SqlCursor
    
    Cursor de bae de datos, que funciona a partir de modelos de Qt.
    Gestiona un QSqlMetadataModel y almacena una posici�n determinada en el registro.
    
    

"""

BOF = -2
EOF = -1
    
class SqlCursor(QtCore.QObject):
    Insert = 0
    Edit = 1
    Del = 2
    Browse = 3
    _model = None # MetadataModel
    _rownumber = -1 # RowNumber
    selectionChanged = QtCore.pyqtSignal(QtCore.QModelIndex,int)
    currentIndexChanged = QtCore.pyqtSignal(QtCore.QModelIndex)
    
    def __init__(self, metadata, prjconn, action = None):
        QtCore.QObject.__init__(self)
        self.metadata = metadata
        self.prjconn = prjconn
        self._modeAccess = None
        self._mainfilter = ""
        if action:
            self.setAction(action)
    def setAction(self, actionname):
        # TODO: Buscar la acci�n en concreto.
        # TODO: Crear aqu� el metadata.model
        self.action = self.metadata.action_index[actionname]
        self.table = self.metadata.table_index[self.action.table]
        self.model = QSqlMetadataModel(None, self.prjconn.qtdb, self.table)
        self.model.setSort(0,0)
            
    def modeAccess(self): return self._modeAccess
    def setEditMode(self): return self.modeAcess(self.Mode.Edit)
    
    def setMainFilter(self, where_filter):
        self._mainfilter = where_filter
        
    def select(self, where = ""):
        if where and self._mainfilter:
            where = "( %s ) AND ( %s )" % (where,self._mainfilter)
        elif self._mainfilter: 
            where = self._mainfilter
        self.model.select()
        
    def refresh(self,fieldName=None):
        return self.select()
        
 
    def configureViewWidget(self,widget):
        widget.setModel(self.model)
        self.model.autoDelegate(widget)
        selection = widget.selectionModel()
        self.connect(selection, QtCore.SIGNAL("currentRowChanged(QModelIndex,QModelIndex)"), self.indexChanged)
        self.connect(self, QtCore.SIGNAL("selectionChanged(QModelIndex,int)"), 
            selection, QtCore.SLOT("select(QModelIndex,SelectionFlags)"))
        self.connect(self, QtCore.SIGNAL("currentIndexChanged(QModelIndex)"), 
            widget, QtCore.SLOT("setCurrentIndex(QModelIndex)"))
        
        new = self.model.index(self._rownumber, 0)
        F = QtGui.QItemSelectionModel
        flags = F.Clear | F.Select | F.Rows | F.Current
        self.selectionChanged.emit(new, flags)
        self.currentIndexChanged.emit(new)
    
    def indexChanged(self, new, old):
        #print "*"
        newrow, oldrow = (new.row(), old.row())
        if newrow != self._rownumber: 
            oldnumber = self._rownumber
            self._rownumber = newrow
            F = QtGui.QItemSelectionModel
            flags = F.Clear | F.Select | F.Rows | F.Current
            self.selectionChanged.emit(new, flags)
            self.currentIndexChanged.emit(new)
            #self.emit(QtCore.SIGNAL("selectionChanged(QModelIndex,int)"), new, flags)
            #print "changed: %d -> %d" % (oldnumber,newrow)
             
    def commitBuffer(self):
        # Commit changes for the current row
        pass
    
    def refreshBuffer(self):
        # Discard changes for the current row
        pass
        
        
        
    """
Slots p�blicos
int 	modeAccess () const
bool 	setEditMode ()
QString 	mainFilter () const
void 	setMainFilter (const QString &f)
void 	setModeAccess (const int m)
void 	setAtomicValueBuffer (const QString &fN, const QString &functionName)
void 	setValueBuffer (const QString &fN, const QVariant &v)
QVariant 	valueBuffer (const QString &fN) const
QVariant 	valueBufferCopy (const QString &fN) const
bool 	isNull (const QString &name) const
void 	setNull (const QString &name)
bool 	isCopyNull (const QString &name) const
void 	setCopyNull (const QString &name)
void 	setEdition (const bool b)
void 	setBrowse (const bool b)
bool 	fieldDisabled (const QString &fN)
bool 	inTransaction ()
bool 	transaction (bool lock)
bool 	rollback ()
bool 	commit ()
void 	setAskForCancelChanges (bool a)
void 	setActivatedCheckIntegrity (bool a)
void 	setActivatedCommitActions (bool a)
bool 	checkIntegrity (bool showError=true)
void 	refresh (QString fN=QString::null)
bool 	refreshBuffer ()
int 	at ()
bool 	seek (int i, bool relative=false, bool emite=false)
bool 	next (bool emite=true)
bool 	prev (bool emite=true)
bool 	first (bool emite=true)
bool 	last (bool emite=true)
int 	del (bool invalidate=true)
bool 	select (const QString &filter, const QSqlIndex &sort=QSqlIndex())
bool 	select ()
int 	size ()
bool 	commitBuffer ()
bool 	commitBufferCursorRelation ()
FLSqlCursorInterface * 	cursorRelation ()
void 	setContext (QObject *c)
QObject * 	context () const
FLSqlCursor * 	obj ()
void 	emitNewBuffer ()
void 	emitBufferChanged (QString v)
void 	emitCursorUpdated ()
void 	emitRecordChoosed ()
void 	emitCurrentChanged (int v)
void 	emitAutoCommit ()
void 	emitBufferCommited ()
QString 	action ()
void 	setAction (QString action)
void 	setUnLock (const QString &fN, bool v)
bool 	isLocked ()
void 	editRecord ()
void 	chooseRecord ()
QString 	table () const
const int 	fieldType (const QString &fN) const
QString 	primaryKey () const
bool 	isValid () const
bool 	isModifiedBuffer ()

Se�ales
void 	newBuffer ()
void 	bufferChanged (QString)
void 	cursorUpdated ()
void 	recordChoosed ()
void 	currentChanged (int)
void 	autoCommit ()
void 	bufferCommited ()

M�todos p�blicos
 	FLSqlCursorInterface (const QString &n)
 	FLSqlCursorInterface (FLSqlCursor *obj)
 	~FLSqlCursorInterface ()
void 	setObj (FLSqlCursor *obj)    
    """
    
    
    """
    :::Codigo de ejemplo::::
:      var curArticulo:FLSqlCursor = new FLSqlCursor("articulos");
-      curArticulo.select("referencia = '" + referencia + "'");
-      if (curArticulo.first()) {
-              curArticulo.setModeAccess(curArticulo.Edit);
-              curArticulo.refreshBuffer();
-              curArticulo.setValueBuffer("costemedio", cM);
-              curArticulo.commitBuffer();
-      }
-

    
    """