from urllib.error import HTTPError

from psycopg import DatabaseError
from league_postgres import load_dotenv
from league_postgres import db_name
from league_postgres import db_host
from league_postgres import db_password
from league_postgres import db_port
from league_postgres import db_user
from league_postgres import headers
from league_postgres import API_key
import requests
import psycopg
import time

def worker_champion():
    while True:
        try:
            version = get_latest_version()
            champion_list = get_champion_information(version)
            insert_into_champion(champion_list)
            print("data has been succesful insertet")
            time.sleep(3600)
        except KeyboardInterrupt:
            return "programm is closing..."


# Champion data can varuy from patch to patch (for example a new champion gets added)
# the data drageon version endpoint from riont delivers a list with all league of legends
# patches while index 0 is always the latest version
def get_latest_version():
    try:
        version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json",headers=headers)
        version_json = version.json()
    except HTTPError:
        return "server error"
    return version_json[0]


# this data dragon endpoint from riot returns specific champion information from this current
# version, this function filters the champion name and key for every champion and stores this in
# a list of tupels.
def get_champion_information(version):
    try:
        champions = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json")
        champions_json = champions.json()
        champ_id_list =  [(champ_data["name"],int(champ_data["key"])) for champ_data in champions_json["data"].values()]
    except HTTPError:
        return "error"
    return champ_id_list

def insert_into_champion(champ_list):
    with psycopg.connect(f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}") as con:
        try:
            with con.cursor() as cur:
                query = "INSERT INTO Champions(champion_name,champion_id) VALUES (%s,%s) ON CONFLICT(champion_id) DO NOTHING"
                cur.executemany(query,champ_list)
                con.commit()


        except DatabaseError:
            return "database error"



if __name__ == "__main__":
    load_dotenv()
    worker_champion()
