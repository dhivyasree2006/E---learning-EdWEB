try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.orm import sessionmaker
    print("Successfully imported SQLAlchemy components.")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
