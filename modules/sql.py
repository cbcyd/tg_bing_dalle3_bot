# Required imports from sqlalchemy for database interactions
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String

# Define the database connection string
sqlite_database = "sqlite:///messages.db"
# Create an engine instance
engine = create_engine(sqlite_database)

# Base class for our ORM models
class Base(DeclarativeBase): pass

# Messages ORM model
class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)  # ID of the message
    thread_id = Column(String)  #  ID of the thread to which the message belongs
    role = Column(String)  # Role of the person who sent the message
    content = Column(String)  # Content of the message

# Create all tables in the database which are defined as DeclarativeBase
Base.metadata.create_all(bind=engine)

# Function to add a new message
def add_message(thread_id, role, content):
    # Start a session with the engine
    with Session(autoflush=False, bind=engine) as db:
        # Create a new message instance
        message = Messages(thread_id=thread_id, role=role, content=content)
        # Add the message instance to the session
        db.add(message)
        # Commit the session to write the changes to database
        db.commit()

# Function to read a thread by ID
def read_thread(thread_id):
    # Initialize an empty array for the thread
    thread = []
    # Start a session with the engine
    with Session(autoflush=False, bind=engine) as db:
        # Query all messages belonging to the thread_id
        messages = db.query(Messages).filter(Messages.thread_id == thread_id)
        # Loop through messages and append them to thread array
        for message in messages:
            thread.append({"role": message.role, "content": message.content})
    # Return the array containing thread messages
    return thread