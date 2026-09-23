-- shows the hole Player
SELECT * FROM Player;


SELECT
    Player.player_name,Player.level,Match_Stats.mvp
FROM
    Player
INNER JOIN Match_Stats USING (puuid);


UPDATE player
SET ranked_winrate = DEFAULT

