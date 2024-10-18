from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from datetime import datetime


class Messages(Model):

    __keyspace__ = "chat"

    urn = columns.Text(primary_key=True)
    chat_urn = columns.Text(primary_key=True, partition_key=True)
    time_stamp = columns.DateTime(
        primary_key=True, default=datetime.now, clustering_order="DESC"
    )
    text = columns.Text()
    sender_urn = columns.Text(index=True)
    receiver_urn = columns.Text(index=True)
    sender_name = columns.Text()
    receiver_name = columns.Text()
    message_type = columns.Text()
    chat_type = columns.Text()
    metadata = columns.Map(columns.Text, columns.Text)
    is_deleted = columns.Boolean(default=False)
    is_read = columns.Boolean(default=False)
    priority = columns.Integer(default=0)
