import json
import psycopg2
from sentence_transformers import SentenceTransformer

from config import DATA_PATH, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST

with open(DATA_PATH + 'custom_members.json', 'r') as file:
    data = json.load(file)

# Initialize the sentence-transformer model
model = SentenceTransformer("multi-qa-mpnet-base-cos-v1")

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST
)

# Create a cursor object
cur = conn.cursor()

# Iterate over each custom member and insert them into the database
for member in data['custom_members']:
    drilldown_name = member['drilldown_name']
    dimension = member['dimension']
    drilldown = member['drilldown']
    drilldown_id = member['drilldown_id']
    cube_names = member['cube_name']
    
    # Calculate the embedding for the product name
    embedding = model.encode(drilldown_name).tolist()
    
    # Insert into the database for each cube_name
    for cube_name in cube_names:
        cur.execute(
            """
            INSERT INTO chat.drilldowns (drilldown_id, drilldown_name, cube_name, drilldown, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (drilldown_id, drilldown_name, cube_name, drilldown, embedding)
        )

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()
