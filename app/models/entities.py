from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):  # noqa: ANN001
        if isinstance(v, ObjectId):
            return v
        return ObjectId(str(v))


class EncryptedText(BaseModel):
    nonce_b64: str
    ciphertext_b64: str


class AnalysisCreate(BaseModel):
    header_text: Optional[str] = None
    # if file is uploaded, header_text may be omitted


class Analysis(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_sub: str
    header_enc: Optional[EncryptedText] = None
    eml_file_id: Optional[PyObjectId] = None
    status: Literal["pending", "completed", "failed"] = "pending"
    result: Optional[dict] = None

    @field_serializer("id", when_used="json")
    def _serialize_id(self, v: Optional[ObjectId]):  # noqa: ANN001
        return str(v) if v is not None else None

    @field_serializer("eml_file_id", when_used="json")
    def _serialize_eml_file_id(self, v: Optional[ObjectId]):  # noqa: ANN001
        return str(v) if v is not None else None

