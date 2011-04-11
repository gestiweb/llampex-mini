import model # import Project, metadata, engine, session

def connect(dboptions):
    from sqlalchemy import create_engine
    conn_url = 'postgresql://%(dbuser)s:%(dbpasswd)s@%(dbhost)s:%(dbport)d/%(dbname)s' % dboptions
    #print conn_url
    model.engine = create_engine(conn_url, echo=True)
    model.Base.metadata.bind = model.engine
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=model.engine)
    # create a Session
    model.session = Session()

def main():
    dboptions = {
            'dbname' : "llampex",
            'dbuser' : "llampexuser",
            'dbpasswd' : "llampexpasswd",
            'dbhost' : "127.0.0.1",
            'dbport' : 5432
            }
    connect(dboptions)

def create_all():
    model.Base.metadata.create_all()

if __name__ == "__main__":
    main()
    create_all()
    