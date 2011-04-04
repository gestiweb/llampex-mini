import model 
import project

def start():
    projects = model.session.query(model.Project)
    for prj in projects:
        project.Project(prj)
        
    
