from datetime import datetime
from sqlalchemy.orm import Session
#
from models.user import User
#
from abstractions.repository import IRepository


class UserRepository(IRepository):

    def __init__(self, urn:str = None, user_urn:str = None, api_name:str = None, session:Session = None):
        super().__init__(urn, user_urn, api_name)
        self.urn = urn
        self.user_urn = user_urn
        self.api_name = api_name
        self.session = session

        if not self.session:
            raise RuntimeError("DB session not found")
        
    def create_record(self, user: User) -> User:

        start_time = datetime.now()
        self.session.add(user)
        self.session.commit()

        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return user

    def retrieve_record_by_email_and_password(
        self, 
        email: str, 
        password: str,
        is_deleted: bool = False
    ) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(
            User.email == email, 
            User.password == password, 
            User.is_deleted == is_deleted
        ).first()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record if record else None

    def retrieve_record_by_email(
        self, 
        email: str,
        is_deleted: bool = False
    ) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(
            User.email == email,
            User.is_deleted == is_deleted
        ).first()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record if record else None

    def retrieve_record_by_id(self, id: str, is_deleted: bool = False) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(User.id == id, User.is_deleted == is_deleted).first()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record if record else None
    
    def retrieve_record_by_urn(self, urn: str, is_deleted: bool = False) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(User.urn == urn, User.is_deleted == is_deleted).first()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record if record else None

    def retrieve_record_by_email_and_is_logged_in(self, email: str, is_logged_in: bool, is_deleted: bool = False) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(User.email == email, User.is_logged_in == is_logged_in, User.is_deleted == is_deleted).one_or_none()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record
    
    def retrieve_record_by_id_is_logged_in(self, id: int,  is_logged_in: bool, is_deleted: bool = False) -> User:

        start_time = datetime.now()
        record = self.session.query(User).filter(User.id == id, User.is_logged_in == is_logged_in, User.is_deleted == is_deleted).one_or_none()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return record
    
    def retrieve_record_by_is_logged_in(self, is_logged_in: bool, is_deleted: bool = False) -> User:

        start_time = datetime.now()
        records = self.session.query(User).filter(User.is_logged_in == is_logged_in, User.is_deleted == is_deleted).all()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return records

    def update_record(self, id: str, new_data: dict) -> User:

        start_time = datetime.now()
        user = self.session.query(User).filter(User.id == id).first()

        if not user:
            raise ValueError(f"User with id {id} not found")
        
        for attr, value in new_data.items():
            setattr(user, attr, value)

        self.session.commit()
        end_time = datetime.now()
        execution_time = end_time - start_time
        self.logger.info(f"Execution time: {execution_time} seconds")

        return user