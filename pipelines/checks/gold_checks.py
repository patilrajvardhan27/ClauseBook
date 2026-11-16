# Pandera checks for the gold layer: every segment needs real boundaries.
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema

GOLD_SEGMENT_SCHEMA = DataFrameSchema(
    {
        "contract_id": Column(str, nullable=False),
        "start_char": Column(int, checks=pa.Check.ge(0)),
        "end_char": Column(int, checks=pa.Check.ge(0)),
        "text": Column(str, nullable=False, checks=pa.Check(lambda s: s.str.len() > 0)),
    },
    strict=False,
)


# Validates a gold-layer dataframe of segments and checks start/end ordering.
def validate_gold_segments(df: pd.DataFrame) -> pd.DataFrame:
    df = GOLD_SEGMENT_SCHEMA.validate(df)
    if (df["end_char"] < df["start_char"]).any():
        raise ValueError("Found a segment whose end_char precedes its start_char")
    return df
