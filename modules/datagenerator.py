import datetime
import os
import sys

import pandas as pd

PROJECT_FOLDER = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_FOLDER)
sys.path.insert(0, PROJECT_FOLDER)
from settings import datagenerator as settings


def __get_SAP_extract():
    """
    Returns a Pandas dataframe containing the data extracted from SAP HR
    """
    df = pd.read_excel(
        settings.EXCEL_FILE_PATH,
        sheet_name=settings.SAP_RH_EXPORT_SHEETNAME,
        usecols=["Unité", "N° SCIPER", "Fonction Interne", "Date de naissance"],
        dtype={"Unité": str, "N° SCIPER": str, "Fonction Interne": str},
        converters={"Date de naissance": pd.to_datetime},
    )
    df.rename(
        columns={
            "Unité": "CF",
            "N° SCIPER": "sciper",
            "Fonction Interne": "position",
            "Date de naissance": "DoB",
        },
        inplace=True,
    )
    df = df[df["position"] == "Professeur"]
    df.drop(columns=["position"], inplace=True)
    return df


def __get_faculty_members():
    """
    Returns a Pandas datafrane containing the faculty members list maintained by A. Barras
    """
    df = pd.read_excel(
        settings.EXCEL_FILE_PATH,
        header=1,
        sheet_name=settings.FACULTY_MEMBERS_SHEETNAME,
        dtype={"SCIPER": str, "Titre": str},
        converters={"Date nomination": pd.to_datetime},
    )
    df.rename(
        columns={
            "SCIPER": "sciper",
            "Titre": "academic rank",
            "Date nomination": "appointment",
        },
        inplace=True,
    )
    return df


def __dump_to_cache(df):
    """
    dumps the current DataFrame to a pickle file for later use
    """
    df.to_pickle(settings.CACHE_FILE_PATH)


def get_data():
    """
    Returns the cached data from disk
    """
    return pd.read_pickle(settings.CACHE_FILE_PATH)


def main():
    sap = __get_SAP_extract()
    faculty_members = __get_faculty_members()
    result = sap.merge(faculty_members, on="sciper", how="left")
    __dump_to_cache(result)


if __name__ == "__main__":
    main()
