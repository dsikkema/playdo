create table conversation (
    id integer primary key autoincrement,
    created_at datetime default current_timestamp,
    updated_at datetime default current_timestamp,
    messages text not null -- json array of messages represented as plain string
);

