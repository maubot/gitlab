from mautrix.util.async_db import Connection, UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute(
        f"""CREATE TABLE IF NOT EXISTS token (
            user_id            VARCHAR(255),
            gitlab_server      TEXT,
            api_token          TEXT NOT NULL,

            PRIMARY KEY (user_id, gitlab_server)
        )"""
    )
    await conn.execute(
        f"""CREATE TABLE IF NOT EXISTS alias (
            user_id            VARCHAR(255),
            gitlab_server      TEXT,
            alias              TEXT,

            PRIMARY KEY (user_id, gitlab_server, alias),
            FOREIGN KEY (user_id, gitlab_server) REFERENCES token (user_id, gitlab_server) ON DELETE CASCADE
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS "default" (
            user_id            VARCHAR(255),
            gitlab_server      TEXT NOT NULL,

            PRIMARY KEY (user_id),
            FOREIGN KEY (user_id, gitlab_server) REFERENCES token (user_id, gitlab_server) ON DELETE CASCADE
        )"""
    ) # add gitlab in primary key ?
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS default_repo (
            room_id            VARCHAR(255),
            server             VARCHAR(255) NOT NULL,
            repo               VARCHAR(255) NOT NULL,

            PRIMARY KEY (room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS matrix_message (
            message_id             VARCHAR(255),
            room_id                VARCHAR(255),
            event_id               VARCHAR(255) NOT NULL,

            PRIMARY KEY (message_id, room_id)
        )"""
    )
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS webhook_token (
            room_id                TEXT NOT NULL,
            secret                 TEXT,

            PRIMARY KEY (secret)
        )"""
    )
