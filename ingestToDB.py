'''
Import Source Sale file
Perform required column check, duplicate and non null invoice check
Ingest into SQL table
'''
from dotenv import load_dotenv
from pathlib import Path
import logging
import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy import URL

#logger
logging.basicConfig(level=logging.INFO,format="%(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

#environment variable
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

#source file name
sourceFileNM = Path(__file__).resolve().parent /"online_saleData.csv"

#DB connnection
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

connURL = URL.create('mysql+pymysql',username= DB_USER,password=DB_PASSWORD,host=DB_HOST,database=DB_NAME)


#pipeline work
try:
    df = pd.read_csv(sourceFileNM, dtype={"InvoiceNo": str, "StockCode": str},
                 parse_dates=["InvoiceDate"])
    if df is None:
        raise KeyError("Source File is empty Or Import error.")
    else:
        logger.info("Data imported successfully\n%s",df.shape)
        logger.info("Records at source:\n%s",len(df))
except FileNotFoundError as err:
    logger.info("Import error occured:\n%s",err)

#header standardisation
df.columns = (df.columns
                .str.strip()
                .str.replace(r'[^a-zA-z0-9]+','_',regex=True))
#required column check
required_cols = ['InvoiceNo','StockCode']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise KeyError(f"Required missing at source:\n {missing_cols}")
#duplicate records
if df.duplicated().sum()>0:
    logger.info("Duplicate record count at source file:%s",df.duplicated().sum())
    logger.info("Dropping duplicates")
    df.drop_duplicates(keep='last',inplace=True)
else:
    logger.info("No duplicates found at source moving to next check.")
#null InvoiceNo or negative quantity
quality_chck = df['InvoiceNo'].isna()|(df['Quantity']<0)
if quality_chck.any:
    logger.info("Quarantine invalid records%s", quality_chck.sum())
    df_qrtn = df[quality_chck].copy()
    df_qrtn.to_csv("quarantineSalesData.csv", index = False)
df = df[~quality_chck]
logger.info("Valid records remaining: %s", len(df))

#ingestion
logger.info("Records to be inserted:\n%s",len(df))
con_engine = create_engine(connURL)
df.to_sql('online_saledata',con=con_engine,if_exists="replace",index=False)