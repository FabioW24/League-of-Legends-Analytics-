CREATE OR REPLACE FUNCTION detect_records()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO Player_Records (puuid,kill_record,cs_record,vision_record)
    VALUES (NEW.puuid,DEFAULT,DEFAULT,DEFAULT)
    ON CONFLICT (puuid) DO NOTHING;
    UPDATE Player_Records
        SET
            kill_record = GREATEST(kill_record, NEW.kills),
            cs_record = GREATEST(cs_record, NEW.cs_per_minute),
            vision_record = GREATEST(vision_record, NEW.vision_score)
        WHERE puuid = NEW.puuid;

    RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION update_winrate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    win_ INTEGER;
    all_games INTEGER;
BEGIN
    SELECT count(m.puuid) INTO win_
    FROM Match_Stats AS m
    WHERE m.win = TRUE AND m.puuid = NEW.puuid;


    SELECT count(m.puuid) INTO all_games
    FROM Match_Stats AS m
    WHERE m.puuid = New.puuid;


    UPDATE Player
       SET ranked_winrate = (win_ * 100.00) / all_games
       WHERE puuid = NEW.puuid;
    RETURN NEW;
    END $$;
