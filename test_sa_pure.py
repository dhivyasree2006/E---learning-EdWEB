from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class TestTable(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String)

engine = create_engine('sqlite:///:memory:') # Use memory for pure test
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Insert
t = TestTable(name="hello")
session.add(t)
session.commit()

# Query
res = session.query(TestTable).all()
print(f"TestTable result: {res[0].id}, {res[0].name}")
