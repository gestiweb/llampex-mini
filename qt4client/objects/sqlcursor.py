# encoding: UTF-8
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
class cursorModes(object):
    Insert = 0
    Edit = 1
    Del = 2
    Browse = 3
    
class SqlCursor(object):
    Mode = cursorModes() # enum  	Mode { Insert = 0, Edit = 1, Del = 2, Browse = 3 }
    _model = None # MetadataModel
    _rownumber = None # RowNumber
    
    def __init__(self, action = None):
        self._modeAccess = None
        self._mainfilter = ""
        if action:
            self.setAction(self.action)
    def setAction(self, actionname):
        # TODO: Buscar la acción en concreto.
        # TODO: Crear aquí el metadata.model
        self._model = None
    
    def modeAccess(self): return self._modeAccess
    def setEditMode(self): return self.modeAcess(self.Mode.Edit)
    
    def setMainFilter(self, where_filter):
        self._mainfilter = where_filter
        
    def select(self, where = ""):
        if where and self._mainfilter:
            where = "( %s ) AND ( %s )" % (where,self._mainfilter)
        elif self._mainfilter: 
            where = self._mainfilter
        # TODO: Re-select all the data from the model.
        
    def refresh(self,fieldName=None):
        return self.select()
        
    
    """
Slots públicos
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

Señales
void 	newBuffer ()
void 	bufferChanged (QString)
void 	cursorUpdated ()
void 	recordChoosed ()
void 	currentChanged (int)
void 	autoCommit ()
void 	bufferCommited ()

Métodos públicos
 	FLSqlCursorInterface (const QString &n)
 	FLSqlCursorInterface (FLSqlCursor *obj)
 	~FLSqlCursorInterface ()
void 	setObj (FLSqlCursor *obj)    
    """