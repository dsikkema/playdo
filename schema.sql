create table conversation (
    id integer primary key autoincrement,
    created_at datetime default current_timestamp,
    updated_at datetime default current_timestamp
);

create table message (
    id integer primary key autoincrement,
    conversation_id integer not null,
    sequence_number integer not null,  -- Order within conversation
    role text not null check (role in ('user', 'assistant')),
    content text not null,  -- JSON array of content blocks
    created_at datetime default current_timestamp,
    foreign key (conversation_id) references conversation(id),
    unique(conversation_id, sequence_number)  -- Ensures ordering integrity
);

