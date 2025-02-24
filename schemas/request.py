from pydantic import BaseModel
from uuid import UUID
class ResumeRecommendRequest(BaseModel):
    message: str

class ResumeExtractRequest(BaseModel):
    user_id: str
    resume_id: str
    file_path: str
