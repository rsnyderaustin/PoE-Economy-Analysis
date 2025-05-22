

def flatten_data_into_rows(datas: list[dict]) -> dict:
    rows_data = dict()
    rows = 0
    for new_data in datas:
        new_cols = [col for col in new_data if col not in rows_data]
        new_cols_dict = {col: [None] * rows for col in new_cols}
        rows_data.update(new_cols_dict)

        for col in rows_data:
            new_val = new_data.get(col, None)
            rows_data[col].append(new_val)

        rows += 1

    # This can be removed at some point. Just error for checking for a possible issue I faced previously
    all_none_cols = {col: val for col, val in rows_data.items() if all(v is None for v in val)}
    if all_none_cols:
        raise ValueError(f"flatten_listing returned columns {all_none_cols.keys()} with all Nones. Invalid because "
                         f"psql cannot determine the datatype for a blank column.")

    return rows_data
