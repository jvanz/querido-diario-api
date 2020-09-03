from datetime import date
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from gazettes import GazetteAccessInterface, GazetteRequest

app = FastAPI()


class GazetteItem(BaseModel):
    territory_id: str
    date: date
    url: str


@app.get("/gazettes/{territory_id}", response_model=List[GazetteItem])
async def get_gazettes(
    territory_id: str, since: Optional[date] = None, until: Optional[date] = None
):
    gazettes = app.gazettes.get_gazettes(
        GazetteRequest(territory_id, since=since, until=until)
    )
    if gazettes:
        return [GazetteItem(**gazette) for gazette in gazettes]
    return []


def set_gazette_interface(gazettes: GazetteAccessInterface):
    if not isinstance(gazettes, GazetteAccessInterface):
        raise Exception("Only GazetteAccessInterface object are accepted")
    app.gazettes = gazettes
