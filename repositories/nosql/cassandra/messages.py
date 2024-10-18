from cassandra.cqlengine.management import sync_table

from abstractions.repository import IRepository

from models.nosql.cassandra.messages import Messages

from start_utils import casssandra_connection, MESSAGE_TTL


class MessagesRepository(IRepository):

    def __init__(self, urn: str = None):
        super().__init__(urn)
        self.urn = urn
        self.key_space = "chat"

        try:
            self.session = casssandra_connection()
            sync_table(Messages)
        except Exception as err:
            self.logger.error(f"Error occured while connection cassanda key space: {self.key_space}. err: {str(err)}")

        self.logger.info(f"Connected to Cassandra keyspace: {self.key_space}")

    def create_record(
        self,
        urn: str,
        chat_urn: str,
        text: str, 
        sender_urn: str, 
        receiver_urn: str, 
        sender_name: str, 
        receiver_name: str, 
        message_type: str, 
        chat_type: str, 
        metadata: dict,
        is_deleted: bool = False,
        is_read: bool = False,
        priority: int = 0
    ):

        try:
    
            message = Messages.ttl(MESSAGE_TTL).create(
                urn=urn,
                chat_urn=chat_urn,
                text=text,
                sender_urn=sender_urn,
                receiver_urn=receiver_urn,
                sender_name=sender_name,
                receiver_name=receiver_name,
                message_type=message_type,
                chat_type=chat_type,
                metadata=metadata,
                is_deleted=is_deleted,
                is_read=is_read,
                priority=priority
            )
            self.logger.info(f"Message created with URN: {message.urn}")

            return message
    
        except Exception as err:
            self.logger.error(f"Error creating message: {err}")
            raise

    def fetch_user_messages(self, user_urn: str, chat_type: str = None):
        """
        Fetch all messages where user_urn is either the sender or the receiver.
        
        :param user_urn: The urn of the user (could be sender or receiver)
        :return: Query set of matching records
        """

        try:

            sent_messages_query = Messages.objects.filter(sender_urn=user_urn)
            if chat_type is not None:
                sent_messages_query = sent_messages_query.filter(chat_type=chat_type)
            sent_messages = sent_messages_query.all()

            received_messages_query = Messages.objects.filter(receiver_urn=user_urn)
            if chat_type is not None:
                received_messages_query = received_messages_query.filter(chat_type=chat_type)
            recieved_messages = received_messages_query.all()

            all_messages = list(sent_messages) + list(recieved_messages)
            all_messages.sort(key=lambda x: x.time_stamp, reverse=True)

            self.logger.info(f"Fetched {len(all_messages)} messages for user_urn: {user_urn} and chat_type: {chat_type}")
            
            return all_messages

        except Exception as err:
            self.logger.error(f"Error fetching messages for user_urn: {user_urn} and chat_type: {chat_type}. Error: {err}")
            raise

    def delete_messages_by_chat_urn(self, chat_urn: str) -> bool:
        """
        Delete all messages in a specific chat identified by chat_urn.
        """
        try:

            Messages.objects.filter(chat_urn=chat_urn).delete()
            self.logger.debug(f"Deleted chat for chat_urn: {chat_urn}")
    
            return True

        except Exception as err:

            self.logger.error(f"Error deleting messages for chat_urn {chat_urn}: {err}")
            return False


    def fetch_records_by_chat_urn_and_type(
        self, 
        chat_urn: str, 
        chat_type: str
    ):
        try:

            messages = Messages.objects(
                urn=chat_urn, 
                chat_type=chat_type
            ).all()
            self.logger.info(f"Fetched {len(messages)} messages for chat_urn: {chat_urn} and chat_type: {chat_type}")

            return messages
            
        except Exception as err:
            self.logger.error(f"Error fetching messages for chat_urn: {chat_urn} and chat_type: {chat_type}. Error: {err}")
            raise
