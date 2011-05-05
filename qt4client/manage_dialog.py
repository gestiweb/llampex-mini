from PyQt4 import QtGui, QtCore, uic
import bjsonrpc
from bjsonrpc.exceptions import ServerError

class ManageDialog(QtGui.QDialog):
    def __init__(self, conn, ui_filepath):
        
        # Prepare Dialog
        QtGui.QDialog.__init__(self)
        self.ui = uic.loadUi(ui_filepath,self) # Cargamos un fichero UI externo
        
        # Prepare Connection
        self.conn = conn
        
        # Call to the ManageProjects Class
        self.manageProjects = self.conn.call.getManageProjects()

        # Class attributes
        self.tableProjects = self.ui.table_projects
        self.tableUsers = self.ui.table_users
        self.forceNoChange = False        
        
        #fill
        users = self.manageProjects.call.getUsers()
        self.fillTable(self.tableUsers,users)
        
        # more class attributes
        self.oldUserNames = self.getCol(self.tableUsers,0)
        
        # signals
        self.ui.connect(self.btnExit, QtCore.SIGNAL("clicked(bool)"), self.exit_performed)
        self.ui.connect(self.tableUsers, QtCore.SIGNAL("cellChanged(int,int)"), self.tableUsers_cellChanged)
        self.ui.connect(self.btnAddUser, QtCore.SIGNAL("clicked(bool)"), self.add_user)
        self.ui.connect(self.btnPassWd, QtCore.SIGNAL("clicked(bool)"), self.passWd)
        self.ui.connect(self.btnDelUser, QtCore.SIGNAL("clicked(bool)"), self.del_user)
        
    
    def fillTable(self, table, rows):
        # prepare space for rows
        table.setRowCount(len(rows))
        
        #fill!
        i = 0
        j = 0
        for row in rows:
            for cell in row.values():
                if cell is not None:
                    item = QtGui.QTableWidgetItem(cell)
                    if cell == True:
                        item.setCheckState(QtCore.Qt.Checked)
                        item.setFlags(QtCore.Qt.ItemFlags(48))
                    elif cell == False:
                        item.setCheckState(QtCore.Qt.Unchecked)
                        item.setFlags(QtCore.Qt.ItemFlags(48))
                    table.setItem(i, j, item)
                j+=1
            i+=1
            j=0
            
    def tableUsers_cellChanged(self,row,col):
        if not self.forceNoChange:
            #if is a name, validate
            validate = True
            if col == 0:
                name = unicode(self.tableUsers.item(row,col).text())
                listOfNames = self.getCol(self.tableUsers,col)
                del listOfNames[row]
                for n in listOfNames:
                    if name == n:
                        self.showMessageBox("Error","The name can't be repeated",QtGui.QMessageBox.Critical)
                        print "Error: The name can't be repeated"
                        validate = False
            
            if not validate:
                self.tableUsers.item(row,col).setText(self.oldUserNames[row])
            else:
                user = self.getRow(self.tableUsers,row)
                user.append(self.oldUserNames[row])
                
                #rpc
                self.manageProjects.call.modifyUser(user)
                
                # renovate the oldUserNames
                self.oldUserNames = self.getCol(self.tableUsers,0)
            
    def add_user(self, b):
        # Add a new User
        validate = True
        itemActived = QtGui.QTableWidgetItem("")
        name, ok = QtGui.QInputDialog.getText(self, 'New User', 'Enter user name:')
        if ok:
            if name == "":
                self.showMessageBox("Error","The name is required",QtGui.QMessageBox.Critical)
                print "Error: The name is required"
                validate = False
            else:
                listOfNames = self.getCol(self.tableUsers,0)
                for n in listOfNames:
                    if name == n:
                        self.showMessageBox("Error","This username already exists",QtGui.QMessageBox.Critical)
                        print "Error: The name can't be repeated"
                        validate = False
        else:
            validate = False
        
        if validate:
            password, ok = QtGui.QInputDialog.getText(self, 'New User', 'Enter password:', QtGui.QLineEdit.Password)
            if ok:
                if password == "":
                    self.showMessageBox("Error","The password is required",QtGui.QMessageBox.Critical)
                    print "Error: The password is required"
                    validate = False
            else:
                validate = False
                
        if validate:
            items = QtCore.QStringList()
            items.append("Yes")
            items.append("No")
            active, ok = QtGui.QInputDialog.getItem(self, "New User", "User is actived?", items, 0, False)
            if ok:
                itemActived.setFlags(QtCore.Qt.ItemFlags(48))
                if active == "Yes":
                    active = True
                    itemActived.setCheckState(QtCore.Qt.Checked)
                else:
                    active = False
                    itemActived.setCheckState(QtCore.Qt.Unchecked)
            else:
                validate = False
                
        if validate:
            #All right!
            print name, password, active
            
            #rpc!
            self.manageProjects.call.newUser(unicode(name),unicode(password),unicode(active))
            
            # renovate the oldUserNames
            self.oldUserNames.append(unicode(name))
            
            # Add to table
            self.forceNoChange = True
            self.tableUsers.insertRow(self.tableUsers.rowCount())
            self.tableUsers.setItem(self.tableUsers.rowCount()-1,0,QtGui.QTableWidgetItem(unicode(name)))
            self.tableUsers.setItem(self.tableUsers.rowCount()-1,1,itemActived)
            
            self.showMessageBox("Info","User added correctly",QtGui.QMessageBox.Information)
            self.forceNoChange = False
            
    def passWd(self, b):
        row = self.tableUsers.currentRow()
        if row == -1:
            self.showMessageBox("Change Password","You must select a user",QtGui.QMessageBox.Critical)
        else:
            name = unicode(self.tableUsers.item(row,0).text())
            password, ok = QtGui.QInputDialog.getText(self, 'Change Password', 'Enter new password for '+name+':', QtGui.QLineEdit.Password)
            if ok and password != "":
                self.manageProjects.call.modifyUserPass(unicode(name),unicode(password))
                self.showMessageBox("Info","Password changed correctly",QtGui.QMessageBox.Information)
                
    def del_user(self, b):
        row = self.tableUsers.currentRow()
        if row == -1:
            self.showMessageBox("Delete User","You must select a user",QtGui.QMessageBox.Critical)
        else:
            name = unicode(self.tableUsers.item(row,0).text())
            ok = QtGui.QMessageBox.question(self, "Delete User", "Are you sure you want to delete "+name+"?", 1, 2)
            
            if ok == 1:
                #rpc
                self.manageProjects.call.delUser(name)
                
                # delete the row
                self.forceNoChange = True
                self.tableUsers.removeRow(row)
                self.forceNoChange = False
                
                # renovate the oldUserNames
                self.oldUserNames = self.getCol(self.tableUsers,0)
                
                self.showMessageBox("Info","User deleted correctly",QtGui.QMessageBox.Information)
            
            

    def showMessageBox(self,title,text,icon):
        msgBox = QtGui.QMessageBox()
        msgBox.setText(text)
        msgBox.setWindowTitle(title)
        msgBox.setIcon(icon)
        msgBox.exec_()
        
    def getRow(self,table,row):
        #returns a list with the items of a row
        result = []
        for i in range(table.columnCount()):
            item = table.item(row,i)
            
            if QtCore.Qt.ItemFlags(48) == item.flags():
                #boolean
                if item.checkState() == 2:
                    result.append(True)
                else:
                    result.append(False)
            else:
                #text
                result.append(unicode(item.text()))
        
        return result
    
    def getCol(self,table,col):
        #returns a list with the items of a column
        result = []
        for i in range(table.rowCount()):
            item = table.item(i,col)
            
            if QtCore.Qt.ItemFlags(48) == item.flags():
                #boolean
                if item.checkState() == 2:
                    result.append(True)
                else:
                    result.append(False)
            else:
                #text
                result.append(unicode(item.text()))
        
        return result
        
    def exit_performed(self, b):
        # return to login?
        self.close()
        
        