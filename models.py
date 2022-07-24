from abc import ABC
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
import json
from os import PathLike
from typing import Optional
from pathlib import Path
from random import choices

from mcstatus.pinger import PingResponse
from disnake import File

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

class Minecraft(ABC, Mapping):
    """
    Class that represents a way to say "Minecraft". the `to_kwargs()` method
    returns a dict that can be used for keyword arguments to disnake message
    sending functions, like `**my_minecraft.to_kwargs()`. Or, you can unpack
    instances of this class directly with `**my_minecraft`.
    """
    def __init__(self):
        raise NotImplementedError()

    def to_kwargs(self) -> dict:
        raise NotImplementedError()
    
    def large(self) -> bool:
        raise NotImplementedError()
    
    def __iter__(self):
        return iter(self.to_kwargs())

    def __getitem__(self, item):
        return self.to_kwargs()[item]

    def __len__(self):
        return len(self.to_kwargs())

class TextMinecraft(Minecraft):
    def __init__(self, text: str):
        self.text = text
    
    def to_kwargs(self) -> dict:
        return {"content": self.text}
    
    def large(self):
        return False

class MediaMinecraft(Minecraft):
    def __init__(self, media_path: PathLike, alt_text: str):
        self.media_path = Path(media_path)
        assert self.media_path.exists()
        self.size = self.media_path.stat().st_size
        self.alt_text = alt_text
    
    def to_kwargs(self) -> dict:
        return {
            "file": File(
                self.media_path,
                filename=f"minecraft{self.media_path.suffix}",
                description=self.alt_text
            )
        }
    
    def large(self) -> bool:
        return self.size > 100_000

@dataclass
class ProbabilityZone():
    p: float
    minecrafts: list[Minecraft]

simple_texts = ProbabilityZone(
    0.9,
    [TextMinecraft(x) for x in 
        ["minecraft", "Minecraft", "MINECRAFT", "Mined Craft", 
        "Myncraft", "Minecràft", "M to the I to the N to the E to the C to the R to the A-F-T"]
    ]
)
media = ProbabilityZone(
    0.05,
    [MediaMinecraft(
        "./assets/glitter.gif",
        "the word Minecraft in glittering pink text"
    )]
)
videos = ProbabilityZone(
    0.05,
    [MediaMinecraft(
        "./assets/portal.mp4",
        "a minecraft player attempts to jump into a nether portal placed high above "
        "the ground. as he fails and lands heavily on the ground below, the minecraft "
        "logo fades in over the footage."
    )]
)
zones = [simple_texts, media, videos]

def get_minecraft() -> Minecraft:
    population: list[Minecraft] = []
    weights: list[float] = []
    for zone in zones:
        for minecraft in zone.minecrafts:
            population.append(minecraft)
            weights.append(zone.p/len(zone.minecrafts))
    return choices(population=population, weights=weights, k=1)[0]

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
            [StatusBasics.Player(x.name, x.id) for x in sample]
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

if __name__ == "__main__":
    media = 0
    text = 0
    text_dist = defaultdict(lambda: 0)
    media_dist = defaultdict(lambda: 0)
    test_count = 1000
    for i in range(test_count):
        mc = get_minecraft()
        if "file" in mc:
            media += 1
            media_dist[mc["file"].description] += 1
        elif "content" in mc:
            text += 1
            text_dist[mc["content"]] += 1
    print(f"images {media/test_count:.2%}", f"text {text/test_count:.2%}")
    print([f"{x/text:.2%}" for x in text_dist.values()])
    print([f"{x/media:.2%}" for x in media_dist.values()])
