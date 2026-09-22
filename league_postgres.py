import psycopg
import requests
from psycopg import DatabaseError
from requests import HTTPError
from dotenv import load_dotenv
import os
import sys


# riot games API key lasts for 24 hours

# for safety reasons passwords and keys are stored in a .env file,
# which will be ignored by GitHub, this function trys to find a file
# called .env for me, which allows use all these passwords as variables

load_dotenv()


API_key = os.getenv("RIOT_API_KEY")
db_user = os.getenv("DB_USER")
db_name = os.getenv("DB_NAME")
db_password = os.getenv("DB_PASSWORD")
db_port = os.getenv("DB_PORT")
db_host = os.getenv("DB_HOST")

# header to verify my request
headers = {
   "X-Riot-Token": API_key
}



def main():
    player_name = input("which player do you whant to add ?")
    player_tagline = input("what is the tagline?")
    puuid = get_puuid(player_name,player_tagline)
    add_into_database(puuid[0])



# the puuid is the primary key for every player
# this funtion uses this riot games API link to get the encrypted puuid of our player
def get_puuid(player_name,tag_line):
    try:
        player_request = requests.get(f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{player_name}/{tag_line}",headers=headers)
        player_request_json = player_request.json()
    except HTTPError:
        print("server error")
        pass
    try:
        return player_request_json["puuid"],player_request_json["gameName"]

    except KeyError:
        return "player_not_found"


# this function uses multiple riot games API links which provide essential Player information, all of them need a encrypted puuid of this Player to hand out this information
# everything gets saved in a dictionary, which will than handed be handed to the add_into_database function
def get_player_table(puuid):
    table_information = {}
    try:
        account_information = requests.get(f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}",headers=headers) # provides game_name and tag_line
        account_information_json = account_information.json()
        account_stats_ranked = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}",headers=headers) # provides information about ranked stats

        account_stats_ranked_json = account_stats_ranked.json()
        account_stats_general = requests.get(f"https://euw1.api.riotgames.com/tft/summoner/v1/summoners/by-puuid/{puuid}",headers=headers) # provides player level
        account_stats_genral_json = account_stats_general.json()
        print(account_information_json)


        table_information["gameName"] = account_information_json["gameName"]
        table_information["tagLine"] = account_information_json["tagLine"]
        table_information["level"] = account_stats_genral_json["summonerLevel"]

        for i in range(len(account_stats_ranked_json)):
            if account_stats_ranked_json[i]["queueType"] == "RANKED_SOLO_5x5":
                table_information["rank"] = f"{account_stats_ranked_json[i]["tier"]} {account_stats_ranked_json[i]["rank"]}"



        return table_information
    except HTTPError:
        print("Http error try later")
        pass



# adds a player by puuid into the database
def add_into_database(puuid):
    table_information = get_player_table(puuid)
    with psycopg.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}") as con:

        with con.cursor() as cur:

            try:
                cur.execute(
                    "INSERT INTO Player (puuid,player_tag,player_name,level,rank,starting_time) VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP) ON CONFLICT (puuid) DO UPDATE SET player_name = EXCLUDED.player_name, level = EXCLUDED.level, rank = EXCLUDED.rank",
                    (puuid,table_information["tagLine"],table_information["gameName"],table_information["level"],table_information["rank"])
                )
            except DatabaseError:
                print("Database error")




if __name__ == "__main__":
   load_dotenv()
   print(get_puuid("Bioms O Planty","3732"))
   print(sys.executable)


