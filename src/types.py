from pydantic import BaseModel

class CallMeeting(BaseModel):
    meetingLink: str
