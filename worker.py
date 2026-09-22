from re import Match
from urllib.error import HTTPError

import psycopg
import requests
import time
import json
import datetime
from league_postgres import load_dotenv
from league_postgres import API_key
from league_postgres import headers
from league_postgres import db_name
from league_postgres import db_host
from league_postgres import db_password
from league_postgres import db_port
from league_postgres import db_user
from league_postgres import get_player_table
from psycopg import DatabaseError
from league_postgres import get_player_table
from datetime import datetime
from league_postgres import add_into_database

def worker():
    update_every_player()
    while True:

        # get this list of tupels (puuid, starting time in python object format)
        active_puuids = get_active_puuids()
        print(active_puuids)
        if active_puuids:
            # irretate over the puuids and convert the starting time from python object notation to unix time notation for the riot API
            for i in range(len(active_puuids)):
                try:
                    python_time = active_puuids[i][1]
                    unix_time = int(python_time.timestamp())
                    matches = get_match(active_puuids[i][0],unix_time)

                except KeyError:
                    print("waiting")
                    time.sleep(160)
                    pass

                except HTTPError:
                    print("sleeping")
                    time.sleep(160)
                    pass

                for j in range(len(matches)):

                    try:
                        insert_into_match(matches[j])
                        insert_into_match_stats(matches[j],active_puuids[i][0])

                    except KeyError:
                        print("waiting")
                        time.sleep(160)
                        pass
                    except HTTPError:
                        print("sleeping")
                        time.sleep(160)
                        pass
            time.sleep(3000)

       # the standart riot api only allows a limited amount of api calls every two minutes
       # so if the limit exceeds, another dictionary will be returned from this api call, which leads to KeyError


# returns all puuids with their corresponding starting time as a list of tupels.
def get_active_puuids():
    with psycopg.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}") as con:
        try:
            with con.cursor() as cur:
                cur.execute("SELECT puuid,starting_time FROM Player")
                return cur.fetchall()
        except DatabaseError:
            print("datbase error")
            pass


# outputs a list of the newest 20 ranked matches after the starting time by using players puuid
def get_match(puuid,start_time):
    try:
        match = requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=20&type=ranked&queue=420&startTime={start_time}",headers=headers)
        match_json = match.json()
        return match_json
    except HTTPError:
        print("Http error")
        pass

# performs the api call, which returns most information needed for the match and match_stats table
def match_info_api_call(match_id):
    match_stats = requests.get(f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}", headers=headers)
    match_stats_json = match_stats.json()
    return match_stats_json

# this function calculates information needed for the match table, the match_id is needed for getting all participants of
# this match, with that information, it is possible to calculate the average levele and the average rank of this match
# using the function get_player_table from the previous script
def get_match_table(match_id):
    sum_level = 0
    list_of_ranks = []
    match_table_information = {}

    try:
        match_stats_json = match_info_api_call(match_id)
        participant_list = match_stats_json["metadata"]["participants"]


        for i in range(len(participant_list)):
            participant_information = get_player_table(participant_list[i])
            sum_level = sum_level + participant_information["level"]

            list_of_ranks.append(participant_information["rank"])


        avg_rank = calculate_average_rank(list_of_ranks)
        avg_level = round(sum_level/10)
        game_creation_unix = match_stats_json["info"]["gameCreation"]

        date_time = datetime.fromtimestamp(game_creation_unix/1000)
        game_duration = match_stats_json["info"]["gameDuration"] / 60

        match_table_information["match_id"] = match_id
        match_table_information["match_duration"] = game_duration

        match_table_information["match_date"] = date_time
        match_table_information["average_level"] = avg_level

        match_table_information["average_rank"] = avg_rank
        print(match_table_information)
        return match_table_information

    except HTTPError:
        print("http error")

def calculate_average_rank(ranks):
    rank_value = 0
    count = 0
    ranks_mapping = {
        "WOOD IV": 0,
        "IRON IV ": 1, "IRON III": 2, "IRON II": 3, "IRON I": 4,
        "BRONZE IV": 5, "BRONZE III": 6, "BRONZE II": 7, "BRONZE I":8,
        "SILVER IV": 9, "SILVER III": 10, "SILVER II": 11, "SILVER I": 12,
        "GOLD IV": 13, "GOLD III": 14, "GOLD II": 15, "GOLD I": 16,
        "PLATINUM IV": 17, "PLATINUM III": 18, "PLATINUM II": 19, "PLATINUM I": 20,
        "EMERALD IV": 21, "EMERALD III": 22, "EMERALD II": 23, "EMERALD I": 24,
        "DIAMOND IV": 25, "DIAMOND III": 26, "DIAMOND II": 27, "DIAMOND I": 28,
        "MASTER": 29, "GRANDMASTER": 30, "CHALLENGER": 31
    }
    # replaces the values with the key and the keys with the values in ranks mapping to
    # get our average_rank with our calculated value
    ranks_mapping_reverse = {value : key for key, value in ranks_mapping.items()}
    for i in range(len(ranks)):
        rank_value = rank_value + ranks_mapping[ranks[i]]
        count = count + 1

    average_rank_value = round(rank_value/count)
    return ranks_mapping_reverse[average_rank_value]

# Inserts match data into match_table, which gets the data from the get_match_table function
def insert_into_match(match_id):
    match_information = get_match_table(match_id)
    print(match_information)
    with psycopg.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}") as con:
        try:
            with con.cursor() as cur:
                 cur.execute(
                     "INSERT INTO Match(match_id,average_level,match_date,match_duration,average_rank) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(match_id) DO NOTHING",
                     (match_information["match_id"],match_information["average_level"],match_information["match_date"],
                      match_information["match_duration"],match_information["average_rank"])
                 )

        except DatabaseError:
            print("servre error")

# to get player specific performance data ,we use the same match data riot endpoint as before
# but here the information in a list which can be found by navigating to "info" dicttionary and
# "participant" dictionary within info which contains a list of dictionarys
def get_match_stats_table(match_id,puuid):
    index = 0
    match_stats_data = {}
    try:
        match_stats_json = match_info_api_call(match_id)
        for i in range(len(match_stats_json["info"]["participants"])):
             if match_stats_json["info"]["participants"][i]["puuid"] == puuid: # navigate to the list to find the player
                 index = i

        match_stats_data["puuid"] = puuid
        match_stats_data["match_id"] = match_id
        match_stats_data["champion_id"] =  match_stats_json["info"]["participants"][index]["championId"]

        match_stats_data["role_name"] =  match_stats_json["info"]["participants"][index]["individualPosition"]
        match_stats_data["team_id"] = match_stats_json["info"]["participants"][index]["teamId"]
        match_stats_data["kills"] = match_stats_json["info"]["participants"][index]["kills"]

        match_stats_data["assists"] = match_stats_json["info"]["participants"][index]["assists"]
        match_stats_data["death"] = match_stats_json["info"]["participants"][index]["deaths"]
        match_stats_data["vision_score"] = match_stats_json["info"]["participants"][index]["visionScore"]

        match_stats_data["damage_dealt"] = match_stats_json["info"]["participants"][index]["totalDamageDealtToChampions"]
        match_stats_data["win"] = match_stats_json["info"]["participants"][index]["win"]

        # the last value we need to add in match_stats is the cs_per_minute, this is one of the most important
        # data for a player who wnats to improve, since it measures how well you can farm in league of legens, which
        # is one big aspect of the game (except for supporter, they need a high vision score and kill pariticipation but that is also covered).

        game_duration = match_stats_json["info"]["gameDuration"]/60
        ally_jungle_monsters = match_stats_json["info"]["participants"][index]["totalAllyJungleMinionsKilled"]

        enemy_jungle_monsters = match_stats_json["info"]["participants"][index]["totalEnemyJungleMinionsKilled"]
        total_minions = match_stats_json["info"]["participants"][index]["totalMinionsKilled"]
        cs_per_minute = (ally_jungle_monsters + enemy_jungle_monsters + total_minions) / game_duration

        match_stats_data["cs_per_minute"] = cs_per_minute


    except DatabaseError:
        print("database error")
        pass

    return match_stats_data

# Player name, level and rank can change, so I need a function to update all Players
def update_every_player():
    player_list = get_active_puuids()
    for i in range(len(player_list)):
        add_into_database(player_list[i][0])

def insert_into_match_stats(match_id,puuid):
    match_stats_information = get_match_stats_table(match_id,puuid)
    print(match_stats_information)
    try:
        with psycopg.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}") as con:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO Match_stats(puuid,match_id,champion_id,role_name,team_id,kills,assists,death,vision_score,cs_per_minute,damage_dealt,win) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (match_id,puuid) DO NOTHING",
                    (match_stats_information["puuid"],match_stats_information["match_id"],match_stats_information["champion_id"],match_stats_information["role_name"],
                     match_stats_information["team_id"],match_stats_information["kills"],match_stats_information["assists"],match_stats_information["death"],
                     match_stats_information["vision_score"],match_stats_information["cs_per_minute"],match_stats_information["damage_dealt"],match_stats_information["win"])
                )
    except DatabaseError:
        print(" database error")
        pass



if __name__ == "__main__":
   worker()
