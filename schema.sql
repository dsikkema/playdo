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

create table user (
    id integer not null primary key autoincrement,
    username text not null unique,
    email text not null unique,
    password_hash text not null,
    password_salt text not null,
    is_admin integer not null default 0,
    created_at datetime not null default current_timestamp,
    updated_at datetime not null default current_timestamp
);

-- Trigger to update the updated_at timestamp
create trigger update_user_timestamp
after update on user
begin
    update user set updated_at = current_timestamp where id = NEW.id;
end;
