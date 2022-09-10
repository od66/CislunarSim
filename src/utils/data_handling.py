from typing import List, Optional, Union
import time
import pandas as pd
from core.state import PropagatedOutput
from dataclasses import asdict
from utils.constants import SIM_ROOT
from pathlib import Path


def states_to_df(states: List[PropagatedOutput]) -> pd.DataFrame:
    """Converts [states] to a DataFrame to use for plotting

    Args:
        states (List[PropagatedOutput]): the current state

    Returns:
        pd.DataFrame: a Pandas DataFrame containing the states' data
    """
    dataframes: List[pd.DataFrame] = []
    for output in states:
        flattened_output_dict = pd.json_normalize(asdict(output))
        single_dataframe = pd.DataFrame.from_dict(flattened_output_dict)
        dataframes.append(single_dataframe)

    complete_df = pd.concat(dataframes)
    return complete_df


def df_to_csv(dataframe: pd.DataFrame, path: Optional[Union[str, Path]] = None):
    """Creates and writes the data in [dataframe] into a csv file at [path]

    Args:
        dataframe (pd.DataFrame): Pandas DataFrame containing state data
        path (Optional[Union[str, Path]]): path of the CSV to write the state data to

    """
    if path is None:
        path = SIM_ROOT / "runs"
    dataframe.to_csv(f"{path}/cislunarsim-{int(time.time())}.csv")
