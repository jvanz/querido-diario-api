from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from gazettes import GazetteDataGateway, Gazette

Base = declarative_base()


class GazetteTable(Base):
    __tablename__ = "gazettes"
    id = Column(Integer, primary_key=True)
    territory_id = Column(String)
    date = Column(Date)
    url = Column(String)


class QueridoDiarioDataMapper(GazetteDataGateway):
    def __init__(self, database, user, password, host):
        self._database = database
        self._user = user
        self._password = password
        self._host = host
        self._engine = create_engine(
            f"postgresql://{self._user}:{self._password}@{self._host}/{self._database}"
        )
        self_session = None

    def connect(self):
        Base.metadata.create_all(self._engine)
        Session = sessionmaker(bind=self._engine)
        self._session = Session()

    def close(self):
        self._session.close()
        self._engine.dispose()

    def get_gazettes(self, territory_id=None):
        query = self._session.query(GazetteTable)
        if territory_id:
            query = query.filter(GazetteTable.territory_id == territory_id)
        for row in query:
            yield Gazette(row.territory_id, row.date, row.url)
