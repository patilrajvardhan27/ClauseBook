# Pandera checks for the silver layer: fails loudly on malformed CUAD rows before they reach gold.
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, DataFrameSchema

SILVER_SPAN_SCHEMA = DataFrameSchema(
    {
        "contract_id": Column(str, nullable=False),
        "category": Column(str, nullable=False),
        "span_text": Column(str, nullable=False, checks=pa.Check(lambda s: s.str.len() > 0)),
        "span_start": Column(int, checks=pa.Check.ge(-1)),
    },
    strict=False,
)


# Validates a silver-layer dataframe of CUAD spans against the schema above.
def validate_silver_spans(df: pd.DataFrame) -> pd.DataFrame:
    return SILVER_SPAN_SCHEMA.validate(df)
