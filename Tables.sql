CREATE TABLE Player(
   puuid TEXT,
   player_tag Text ,
   player_name TEXT NOT NULL,
   level INTEGER,
   rank TEXT,
   -- starts counting the winrate after inserting the Player into the Database (wins and losses before starting your analyse journey wont count
   ranked_winrate REAL DEFAULT 0.00,

   CONSTRAINT ref_key_Player PRIMARY KEY (puuid),
   CONSTRAINT uni_player_name UNIQUE (player_name),
   CONSTRAINT val_level CHECK ( level >=1 ),
   CONSTRAINT val_winrate CHECK ( Player.ranked_winrate >= 0 AND ranked_winrate <=100 )
);

CREATE TABLE Match(
    match_id TEXT,
    average_level INTEGER,
    match_date DATE,
    match_duration REAL,
    average_rank TEXT,

    CONSTRAINT ref_key_Match PRIMARY KEY (match_id),
    CONSTRAINT val_avg_level CHECK ( average_level >= 1 ),
    CONSTRAINT val_match_duration CHECK ( match_duration >= 0 )

);
CREATE TABLE Champions(
    champion_id INTEGER,
    champion_name TEXT,


    Constraint ref_key_Champions PRIMARY KEY (champion_id),
    CONSTRAINT uni_champion_name UNIQUE (champion_name)

);
CREATE TYPE ROLES as ENUM ('JUNGLE','TOP','MIDDLE','BOTTOM','UTILITY');



CREATE TABLE Match_Stats(
    puuid TEXT,
    match_id TEXT,
    champion_id INTEGER,
    role_name ROLES,
    team_id INTEGER NOT NULL ,
    kills INTEGER,
    assists INTEGER,
    death INTEGER,
    vision_score SMALLINT,
    cs_per_minute REAL,
    damage_dealt BIGINT,
    win BOOLEAN NOT NULL,
    mvp BOOLEAN DEFAULT FALSE,

    CONSTRAINT ref_key_Match_Stats PRIMARY KEY (puuid,match_id),
    CONSTRAINT ref_fk_Player FOREIGN KEY (puuid) REFERENCES Player (puuid) ON DELETE RESTRICT ,
    CONSTRAINT ref_fk_Champions FOREIGN KEY (champion_id) REFERENCES Champions (champion_id) ON DELETE RESTRICT,
    CONSTRAINT ref_fk_Match FOREIGN KEY (match_id) REFERENCES Match (match_id) ON DELETE RESTRICT,
    CONSTRAINT val_vision_score CHECK ( vision_score >= 0 )
);

CREATE TABLE Player_Records(
    puuid TEXT,
    kill_record SMALLINT DEFAULT 0,
    cs_record SMALLINT DEFAULT 0,
    vision_record SMALLINT DEFAULT 0,

    CONSTRAINT ref_key_Records PRIMARY KEY (puuid),
    CONSTRAINT ref_fk_Records FOREIGN KEY (puuid) REFERENCES Player(puuid) ON DELETE CASCADE
);



