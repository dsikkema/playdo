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
    editor_code text,  -- Code from the editor (null if not applicable)
    stdout text,  -- Standard output (null if not run or not applicable)
    stderr text,  -- Standard error (null if not run or not applicable)
    created_at datetime default current_timestamp,
    foreign key (conversation_id) references conversation(id),
    unique(conversation_id, sequence_number)  -- Ensures ordering integrity
);
