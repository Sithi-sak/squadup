from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for response/request models the frontend consumes directly: fields are declared
    snake_case (matching the DB columns backing them) but serialize/parse as camelCase to line
    up with the existing frontend TS interfaces (stores/players.ts, stores/auth.ts)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
