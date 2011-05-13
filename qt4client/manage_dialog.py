from PyQt4 import QtGui, QtCore, uic
import bjsonrpc
from bjsonrpc.exceptions import ServerError

class ManageDialog(QtGui.QDialog):
    def __init__(self, conn, ui_filepath, np_filepath):
        
        # Prepare Dialog
        QtGui.QDialog.__init__(self)
        self.ui = uic.loadUi(ui_filepath,self) # Cargamos un fichero UI externo
        
        # Prepare Connection
        self.conn = conn
        
        # Call to the ManageProjects Class
        self.manageProjects = self.conn.call.getManageProjects()

        # Class attributes
        self.forceNoChange = False
        self.np_filepath = np_filepath
        self.tableProjects = self.ui.table_projects
        self.tableUsers = self.ui.table_users
        self.comboProjects = self.ui.comboProjects
        self.listActive = self.ui.listActive
        self.listInactive = self.ui.listInactive
        
        #fill
        users = self.manageProjects.call.getUsers()
        projects = self.manageProjects.call.getProjects()
        self.fillTable(self.tableUsers,users)
        self.fillTable(self.tableProjects,projects)
        
        # more class attributes
        self.oldUserNames = self.getCol(self.tableUsers,0)
        self.oldCodes = self.getCol(self.tableProjects,0)
        
        #Projects/Users Fill
        self.fillComboBox()
        
        # signals
        self.ui.connect(self.btnExit, QtCore.SIGNAL("clicked(bool)"), self.exit_performed)
        self.ui.connect(self.tableUsers, QtCore.SIGNAL("cellChanged(int,int)"), self.tableUsers_cellChanged)
        self.ui.connect(self.btnAddUser, QtCore.SIGNAL("clicked(bool)"), self.add_user)
        self.ui.connect(self.btnPassUser, QtCore.SIGNAL("clicked(bool)"), self.changePassUser)
        self.ui.connect(self.btnDelUser, QtCore.SIGNAL("clicked(bool)"), self.del_user)
        self.ui.connect(self.tableProjects, QtCore.SIGNAL("cellChanged(int,int)"), self.tableProjects_cellChanged)
        self.ui.connect(self.btnAddProj, QtCore.SIGNAL("clicked(bool)"), self.add_project)
        self.ui.connect(self.btnPassProj, QtCore.SIGNAL("clicked(bool)"), self.changePassProject)
        self.ui.connect(self.btnDelProj, QtCore.SIGNAL("clicked(bool)"), self.del_project)
        self.ui.connect(self.comboProjects, QtCore.SIGNAL("currentIndexChanged(const QString&)"), self.comboProjects_changed)
        self.ui.connect(self.btnRight, QtCore.SIGNAL("clicked(bool)"), self.rightPerformed)
        self.ui.connect(self.btnLeft, QtCore.SIGNAL("clicked(bool)"), self.leftPerformed)
        self.ui.connect(self.btnAllRight, QtCore.SIGNAL("clicked(bool)"), self.allRightPerformed)
        self.ui.connect(self.btnAllLeft, QtCore.SIGNAL("clicked(bool)"), self.allLeftPerformed)
        self.ui.connect(self.listActive, QtCore.SIGNAL("itemChanged (QListWidgetItem *)"), self.movedToActive)
        self.ui.connect(self.listInactive, QtCore.SIGNAL("itemChanged (QListWidgetItem *)"), self.movedToInactive)
        
    
    def fillTable(self, table, rows):
        # prepare space for rows
        table.setRowCount(len(rows))
        
        #fill!
        i = 0
        j = 0
        for row in rows:
            for cell in row:
                if cell is not None:
                    item = QtGui.QTableWidgetItem(unicode(cell))
                    if cell == True:
                        item.setCheckState(QtCore.Qt.Checked)
                        item.setFlags(QtCore.Qt.ItemFlags(48))
                        item.setText("")
                    elif cell == False:
                        item.setCheckState(QtCore.Qt.Unchecked)
                        item.setFlags(QtCore.Qt.ItemFlags(48))
                        item.setText("")
                    table.setItem(i, j, item)
                j+=1
            i+=1
            j=0
    
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
    
    ###################### USERS ######################            
    def tableUsers_cellChanged(self,row,col):
        if not self.forceNoChange:
            #if is a name, validate
            validate = True
            if col == 0:
                name = unicode(self.tableUsers.item(row,col).text())
                listOfNames = self.getCol(self.tableUsers,col)
                del listOfNames[row]
                if name in listOfNames:
                    self.showMessageBox("Error","The name can't be repeated",QtGui.QMessageBox.Warning)
                    print "Error: The name can't be repeated"
                    validate = False
            if not validate:
                self.tableUsers.item(row,col).setText(self.oldUserNames[row])
            else:
                user = self.getRow(self.tableUsers,row)
                user.append(self.oldUserNames[row])
                
                #rpc
                if not self.manageProjects.call.modifyUser(user):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                
                # renovate the oldUserNames
                self.oldUserNames = self.getCol(self.tableUsers,0)
                
                # renovate ProjectsUsers
                self.fillComboBox()
            
    def add_user(self, b):
        # Add a new User
        validate = True
        
        itemActived = QtGui.QTableWidgetItem("")
        itemAdmin = QtGui.QTableWidgetItem("")
        items = QtCore.QStringList()
        items.append("Yes")
        items.append("No")
        
        name, ok = QtGui.QInputDialog.getText(self, 'New User', 'Enter user name:')
        
        if ok:
            if name == "":
                self.showMessageBox("Error","The name is required",QtGui.QMessageBox.Warning)
                print "Error: The name is required"
                validate = False
            else:
                listOfNames = self.getCol(self.tableUsers,0)
                if name in listOfNames:
                    self.showMessageBox("Error","This username already exists",QtGui.QMessageBox.Warning)
                    print "Error: The name can't be repeated"
                    validate = False
        else:
            validate = False
        
        if validate:
            password, ok = QtGui.QInputDialog.getText(self, 'New User', 'Enter password:', QtGui.QLineEdit.Password)
            if ok:
                if password == "":
                    self.showMessageBox("Error","The password is required",QtGui.QMessageBox.Warning)
                    print "Error: The password is required"
                    validate = False
            else:
                validate = False
                
        if validate:
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
            admin, ok = QtGui.QInputDialog.getItem(self, "New User", "User is administrator?", items, 0, False)
            if ok:
                itemAdmin.setFlags(QtCore.Qt.ItemFlags(48))
                if admin == "Yes":
                    admin = True
                    itemAdmin.setCheckState(QtCore.Qt.Checked)
                else:
                    admin = False
                    itemAdmin.setCheckState(QtCore.Qt.Unchecked)
            else:
                validate = False
                
        if validate: #All right!
            
            #rpc!
            if not self.manageProjects.call.newUser(unicode(name),unicode(password),active,unicode(admin)):
                self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                self.close()
            
            # renovate the oldUserNames
            self.oldUserNames.append(unicode(name))
            
            # Add to table
            self.forceNoChange = True
            self.tableUsers.insertRow(self.tableUsers.rowCount())
            self.tableUsers.setItem(self.tableUsers.rowCount()-1,0,QtGui.QTableWidgetItem(unicode(name)))
            self.tableUsers.setItem(self.tableUsers.rowCount()-1,1,itemActived)
            self.tableUsers.setItem(self.tableUsers.rowCount()-1,2,itemAdmin)
        
            self.showMessageBox("Info","User added correctly",QtGui.QMessageBox.Information)
            self.forceNoChange = False
            
            # renovate ProjectsUsers
            self.fillComboBox()
            
    def changePassUser(self, b):
        row = self.tableUsers.currentRow()
        if row == -1:
            self.showMessageBox("Change Password","You must select a user",QtGui.QMessageBox.Warning)
        else:
            name = unicode(self.tableUsers.item(row,0).text())
            password, ok = QtGui.QInputDialog.getText(self, 'Change Password', 'Enter new password for '+name+':', QtGui.QLineEdit.Password)
            if ok and password != "":
                if not self.manageProjects.call.modifyUserPass(unicode(name),unicode(password)):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                    
                self.showMessageBox("Info","Password changed correctly",QtGui.QMessageBox.Information)
                
    def del_user(self, b):
        row = self.tableUsers.currentRow()
        if row == -1:
            self.showMessageBox("Delete User","You must select a user",QtGui.QMessageBox.Warning)
        else:
            name = unicode(self.tableUsers.item(row,0).text())
            ok = QtGui.QMessageBox.question(self, "Delete User", "Are you sure you want to delete "+name+"?", 1, 2)
            
            if ok == 1:
                #rpc
                if not self.manageProjects.call.delUser(name):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                
                # delete the row
                self.forceNoChange = True
                self.tableUsers.removeRow(row)
                self.forceNoChange = False
                
                # renovate the oldUserNames
                self.oldUserNames = self.getCol(self.tableUsers,0)
                
                self.showMessageBox("Info","User deleted correctly",QtGui.QMessageBox.Information)
                
                # renovate ProjectsUsers
                self.fillComboBox()
    
    ###################### PROJECTS ######################
    def tableProjects_cellChanged(self,row,col):
        if not self.forceNoChange:
            validate = True
            #if is a code, validate
            if col == 0:
                code = unicode(self.tableProjects.item(row,col).text())
                listOfCodes = self.getCol(self.tableProjects,col)
                del listOfCodes[row]
                if code in listOfCodes:
                    self.showMessageBox("Error","The code can't be repeated",QtGui.QMessageBox.Warning)
                    print "Error: The code can't be repeated"
                    validate = False
                    self.tableProjects.item(row,col).setText(self.oldCodes[row])
            #if is a port, validate Integer
            if col == 5:
                try:
                    int(self.tableProjects.item(row,col).text())
                except ValueError:
                    self.showMessageBox("Error","The port must be a number",QtGui.QMessageBox.Warning)
                    validate = False
                    self.forceNoChange = True
                    self.tableProjects.item(row,col).setText("0")
                    self.forceNoChange = False
                    
            if validate:
                proj = self.getRow(self.tableProjects,row)
                proj.append(self.oldCodes[row])
                
                #rpc
                if not self.manageProjects.call.modifyProject(proj):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                
                # renovate the oldCodes
                self.oldCodes = self.getCol(self.tableProjects,0)
                
                # renovate ProjectsUsers
                self.fillComboBox()
        
    def add_project(self, b):
        newWindow = NewProjectDialog(self)
        newWindow.show()
        
    def changePassProject(self,b):
        row = self.tableProjects.currentRow()
        if row == -1:
            self.showMessageBox("Change Password","You must select a project",QtGui.QMessageBox.Warning)
        else:
            code = unicode(self.tableProjects.item(row,0).text())
            password, ok = QtGui.QInputDialog.getText(self, 'Change Password', 'Enter new password for '+code+' project:', QtGui.QLineEdit.Password)
            if ok and password != "":
                if not self.manageProjects.call.modifyProjPass(unicode(code),unicode(password),"None"):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                    
                self.showMessageBox("Info","Password changed correctly",QtGui.QMessageBox.Information)
        
    def del_project(self,b):
        row = self.tableProjects.currentRow()
        if row == -1:
            self.showMessageBox("Delete Project","You must select a project",QtGui.QMessageBox.Warning)
        else:
            code = unicode(self.tableProjects.item(row,0).text())
            ok = QtGui.QMessageBox.question(self, "Delete Project", "Are you sure you want to delete "+code+"?", 1, 2)
            
            if ok == 1:
                #rpc
                if not self.manageProjects.call.delProject(code):
                    self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                    self.close()
                
                # delete the row
                self.forceNoChange = True
                self.tableProjects.removeRow(row)
                self.forceNoChange = False
                
                # renovate the oldUserNames
                self.oldCodes = self.getCol(self.tableProjects,0)
                
                self.showMessageBox("Info","Project deleted correctly",QtGui.QMessageBox.Information)
                
                # renovate ProjectsUsers
                self.fillComboBox()
                
                
    ###################### USERS/PROJECTS ######################
    def fillComboBox(self):
        self.comboProjects.clear()
        self.comboProjects.addItems(self.oldCodes)
        # If exists any project, fill the Lists
        if self.comboProjects.maxCount() != 0:
            self.fillListsUsers(self.comboProjects.itemText(0))
        
    def fillListsUsers(self, project):
        self.fillActiveUsers(project)
        self.fillInactiveUsers(project)
    
    def fillActiveUsers(self, project):
        self.listActive.clear()
        self.listActive.addItems(self.manageProjects.call.getActiveUsers(unicode(project)))
    
    def fillInactiveUsers(self, project):
        self.listInactive.clear()
        self.listInactive.addItems(self.manageProjects.call.getInactiveUsers(unicode(project)))
        
    def comboProjects_changed(self, project):
        # refill the Lists
        self.fillListsUsers(project)
        
    def addUserToProject(self,item):
        user = unicode(item.text())
        code = unicode(self.comboProjects.currentText())
        
        #rpc
        if not self.manageProjects.call.addUserToProject(user,code):
            self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
            self.close()
    
    def delUserFromProject(self,item):
        user = unicode(item.text())
        code = unicode(self.comboProjects.currentText())
        #rpc
        if not self.manageProjects.call.delUserFromProject(user,code):
            self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
            self.close()
        
    def rightPerformed(self,b):
        item = self.listActive.takeItem(self.listActive.currentRow())
        if item == None:
            self.showMessageBox("Manage Users and Projects","You must select a user on Active List",QtGui.QMessageBox.Warning)
        else:
            self.delUserFromProject(item)
            #move item
            self.listInactive.addItem(item)
    
    def leftPerformed(self,b):
        item = self.listInactive.takeItem(self.listInactive.currentRow())
        if item == None:
            self.showMessageBox("Manage Users and Projects","You must select a user on Inactive List",QtGui.QMessageBox.Warning)
        else:
            self.addUserToProject(item)            
            #move item
            self.listActive.addItem(item)
            
    def movedToActive(self,item):
        self.addUserToProject(item)
    
    def movedToInactive(self,item):
        self.delUserFromProject(item)
    
    def allRightPerformed(self,b):
        for i in range(self.listActive.count()):
            item = self.listActive.takeItem(0)
            if not item == None:
                self.delUserFromProject(item)
                #move item
                self.listInactive.addItem(item)
    
    def allLeftPerformed(self,b):
        for i in range(self.listInactive.count()):
            item = self.listInactive.takeItem(0)
            if not item == None:
                self.addUserToProject(item)
                #move item
                self.listActive.addItem(item)


        
    def exit_performed(self, b):
        # return to login?
        self.close()

        
class NewProjectDialog(QtGui.QDialog):
    
    def __init__(self, manageForm):
        
        self.manageForm = manageForm
        
        # Prepare Dialog
        QtGui.QDialog.__init__(self)
        self.ui = uic.loadUi(self.manageForm.np_filepath,self) # Cargamos un fichero UI externo
        
        # Prepare Connection
        self.manageProjects = self.manageForm.manageProjects
        
        self.manageForm.setEnabled(False)
        
        self.ui.connect(self.btnCancel, QtCore.SIGNAL("clicked(bool)"), self.cancel_performed)
        self.ui.connect(self.btnSave, QtCore.SIGNAL("clicked(bool)"), self.save_performed)
        self.ui.connect(self, QtCore.SIGNAL("finished(int)"), self.exit_performed)
    
    def save_performed(self, b):
        #reiniciem l'error
        self.errorLabel.setText("")
        if self.code.text() == "" or self.name.text() == "" or self.db.text() == "" or self.path.text() == "":
            self.errorLabel.setText("Fields with * must be filled.")
        elif self.code.text() in self.manageForm.getCol(self.manageForm.tableProjects,0):
            self.errorLabel.setText("The project code already exists.")
        else: #All right!
            
            active = True if (self.active.currentText() == "Yes") else False
            itemActived = QtGui.QTableWidgetItem("")
            itemActived.setFlags(QtCore.Qt.ItemFlags(48))
            if active == True:
                itemActived.setCheckState(QtCore.Qt.Checked)
            else:
                itemActived.setCheckState(QtCore.Qt.Unchecked)
            
            
            #rpc!
            if  not self.manageProjects.call.newProject(unicode(self.code.text()), unicode(self.name.text()),
            unicode(self.db.text()), unicode(self.path.text()), unicode(self.host.text()), self.port.value(),
            unicode(self.user.text()), unicode(self.password.text()), unicode(self.encrypt.currentText()), active):
                self.showMessageBox("Fatal Error","There is an unexpected error in the database. Exiting...",QtGui.QMessageBox.Critical)
                self.close()
            
            # renovate the oldCodes
            self.manageForm.oldCodes.append(unicode(self.code.text()))
            
            # renovate ProjectsUsers
            self.manageForm.fillComboBox()
            
            # Add to table
            self.manageForm.forceNoChange = True
            self.manageForm.tableProjects.insertRow(self.manageForm.tableProjects.rowCount())
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,0,QtGui.QTableWidgetItem(unicode(self.code.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,1,QtGui.QTableWidgetItem(unicode(self.name.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,2,QtGui.QTableWidgetItem(unicode(self.db.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,3,QtGui.QTableWidgetItem(unicode(self.path.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,4,QtGui.QTableWidgetItem(unicode(self.host.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,5,QtGui.QTableWidgetItem(unicode(self.port.value())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,6,QtGui.QTableWidgetItem(unicode(self.user.text())))
            self.manageForm.tableProjects.setItem(self.manageForm.tableProjects.rowCount()-1,7,itemActived)

            self.manageForm.showMessageBox("Info","Project added correctly",QtGui.QMessageBox.Information)
            self.manageForm.forceNoChange = False
            
            # close addProject form
            self.manageForm.setEnabled(True)
            self.close()
    
    def cancel_performed(self, b):
        self.manageForm.setEnabled(True)
        self.close()
        
    def exit_performed(self, i):
        self.manageForm.setEnabled(True)
        self.close()
        
        