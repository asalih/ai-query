import os
import openai
import sqlite3
import pandas as pd
from zipfile import ZipFile
  
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("API_KEY")
if openai.api_key == "":
    raise Exception("PROVIDE 'openapi' API KEY!")

case_path = os.getenv("CASE_PPC")
if case_path == "":
    raise Exception("PROVIDE PPC FILE!")

with ZipFile(case_path, 'r') as zip:
    # extracting all the files
    print('Extracting db file...')
    zip.extract("Case.db")

print('Opening session.')
connection = sqlite3.connect("Case.db", isolation_level="EXCLUSIVE")

crsr = connection.cursor()
crsr.execute("""SELECT name, sql FROM sqlite_master
    WHERE type='table'
    ORDER BY name;""")

aiPrompt = "### SQLite tables, with their properties and types:\n#"
for row in crsr:
    aiPrompt += "\n#"+row[1].replace("CREATE TABLE", "")

crsr.close()

while True:
    user_input = input("Ask me anything about the data > ")
    if user_input == "exit":
        print("exiting...")
        break

    response = openai.Completion.create(
    model="code-davinci-002",
    prompt=aiPrompt + "\n#\n### A query to "+user_input+"\nSELECT",
    temperature=0,

    max_tokens=150,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop=["#", ";"]
    )

    if len(response.choices) > 0:
        stmt = "SELECT " + response.choices[0].text
        dataFrame = pd.read_sql(stmt, connection)
        print(dataFrame)
