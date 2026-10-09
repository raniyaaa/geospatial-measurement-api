from datetime import datetime

from pydantic import BaseModel, ConfigDict



from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    crs: str | None
    feature_count: int | None
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

#this is needed cuz oru feature contains many data, we dont need all of them in measurement's endpoint.
class MeasurementResponse(BaseModel):
    feature_index: int
    geometry_type: str
    area: float | None
    length: float | None


