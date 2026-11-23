from pydantic import BaseModel, Field

class JudgementIn(BaseModel):
    detection_id: int
    rank: str = Field(pattern="^(AA|A1|A2|B|C|S)$")
    comment: str = ""
    actor: str = "技術者"


class ImagePatch(BaseModel):
    km_m: float | None = None
    structure_id: str | None = None
    member_id: str | None = None
    license: str | None = Field(default=None, pattern="^(client|cc-by|cc0|pd|demo|unknown)$")



class PointPick(BaseModel):
    index: int = Field(ge=0)
    top_k: int = Field(default=3, ge=1, le=5)
    site: str | None = None
