CREATE KEYSPACE chat
    WITH REPLICATION = {
      'class': 'SimpleStrategy',
      'replication_factor': 3
    };

CREATE TABLE chat.messages (
    urn UUID,                    -- Unique identifier for the chat message
    text TEXT,                   -- The content of the message
    time_stamp TIMESTAMP,         -- When the message was sent
    sender_urn UUID,             -- Unique identifier for the sender
    receiver_urn UUID,           -- Unique identifier for the receiver
    sender_name TEXT,            -- Sender's name
    receiver_name TEXT,          -- Receiver's name
    message_type TEXT,           -- Message type (e.g., text, image, video)
    chat_type TEXT,              -- Type of chat (e.g., direct, group)
    metadata MAP<TEXT, TEXT>,    -- Extra metadata (e.g., read status, attachment info)
    is_deleted BOOLEAN,          -- Flag to indicate if the message was deleted
    is_read BOOLEAN,             -- Flag to indicate if the message has been read
    priority INT,                -- Priority of the message (e.g., 0 for normal, 1 for high)
    PRIMARY KEY ((urn), time_stamp)
) WITH CLUSTERING ORDER BY (time_stamp DESC);

ALTER TABLE chat.messages ADD chat_urn text;