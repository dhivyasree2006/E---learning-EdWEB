import models, database
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Enable logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def test():
    # models.Base.metadata.create_all(bind=database.engine)
    db = next(database.get_db())
    print("Querying users...")
    try:
        users = db.query(models.User).all()
        print(f"Users: {len(users)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
