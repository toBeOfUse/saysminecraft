from dataclasses import dataclass
import json
from os import PathLike
from typing import Optional
from pathlib import Path

from mcstatus.pinger import PingResponse

@dataclass
class BotConfig():
    token: str
    mc_server_host: str
    mc_server_port: int
    discord_alert_server_id: int

    @classmethod
    def load_from_files(cls):
        with open("token.txt") as token_file:
            token = token_file.read()
        with open("server.json") as server_file:
            server_data = json.load(server_file)
        return cls(
            token=token,
            mc_server_host=server_data["host"],
            mc_server_port=server_data["port"],
            discord_alert_server_id=server_data["discord_alert_server"]
        )

class StatusBasics():

    class Player():

        def __init__(self, name: str, id: str):
            self.name = name
            self.id = id

        def __hash__(self) -> int:
            return hash(self.id)
        
        def __eq__(self, other: "StatusBasics.Player"):
            return self.id == other.id

        def toDict(self) -> dict:
            return { "name": self.name, "id": self.id }
        
    def __init__(self, online: int, sample: list[PingResponse.Players.Player]):
        self.online = online
        self.sample = (
            [StatusBasics.Player(x.raw) for x in sample]
                if sample is not None
                else []
        )
    
    def __eq__(self, other: "StatusBasics") -> bool:
        return self.online == other.online and self.sample == other.sample
    
    def toDict(self) -> dict:
        return {"online": self.online, "sample": [x.toDict() for x in self.sample]}
    
    @classmethod
    def fromDict(cls, src: dict) -> "StatusBasics":
        return cls(
            src["online"], 
            [PingResponse.Players.Player(x) for x in src["sample"]]
        )
    
    @classmethod
    def fromFile(cls, src: PathLike) -> Optional["StatusBasics"]:
        path = Path(src)
        if not path.exists():
            return None
        else:
            with open(path) as last_status_file:
                return cls.fromDict(json.load(last_status_file))
    
    def toFile(self, to: PathLike) -> None:
        with open(to, mode="w+", encoding="utf-8") as status_file:
            json.dump(self.toDict(), status_file)
