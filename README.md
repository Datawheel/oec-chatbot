# datausa-chat

This repository contains scripts for a chatbot that leverages artificial intelligence to interact with users and gather insights from [DataUSA.io](https://datausa.io/). The chatbot aims to deliver meaningful insights directly from natural language queries, simplifying the process for users to access and analyze data.

## Folders inside **`api/`**

### 1. **`data/`**
   - Contains JSON files featuring few-shot examples tailored for the Language Model (LLM). 

   - Also contains `tables.json` which contains available cubes, with their descriptions, column names, and relevant details.

### 2. **`utils/`**
   - Houses all the main scripts to run the chatbot.
  
   - **Subfolders:**
     1. **`api_data_request/`**
        - Core scripts responsible for constructing the API URL. Contains functions for processing query cuts and matching values with their respective IDs.
     
     2. **`preprocessors/`**
        - Contains scripts that preprocess text (or any other data type as needed).

     3. **`table_selection/`**
        - All scripts needed to lookup the relevant table/cube that contains the data needed to answer a user's query.

     4. **`data_analysis/`**
        - Contains scripts used for data analysis (mainly using [LangChain](https://python.langchain.com/docs/get_started/introduction)).


## General Workflow

### 1. Table Selection

1. Matches the user's Natural Language Query (NLQ) to the table that *should* contain the relevant data to give an answer. To achieve this there are 3 options:

   - **Option 1: get_relevant_tables_from_database()**
     - Utilizes embeddings to match the query with the tables' descriptions in the database using an SQL similarity function.

   - **Option 2: get_relevant_tables_from_LM()**
     - Provides the Language Model (LM) with the names and descriptions of all available tables and asks the LM to choose one.

   - **Option 3: request_tables_to_lm_from_db()**
     - Hybrid approach that obtains the top N matches from the database using embeddings. It then asks the LM to choose between these N tables.

2. All the above functions return the name of the most relevant table. The app currenty works with Option 3.

### 2. API URL Generator & Data Request

   1. Builds a prompt that includes the table to query (with its description and column names) and the NLQ given by the user.

   2. Requests the LM to return a comment explaining why the chosen variables, measures, and filters can answer the query, along with a JSON containing these parameters with the following structure:


```json
     {
        "variables": ["Origin State", "Destination State"],
        "measures": ["Thousands Of Tons"],
        "filters": ["Year = 2020", "SCTG2 = Coal", "Origin State = New York", "Destination State = California"]
     }
```

   3. Extracts the JSON from the LM's output string.

   4. For the cuts, a similarity search is done over the corresponding dimension members to extract their ids.

   5. The API URL (for Mondrian or Tesseract) is built using the processed cuts, drilldowns and measures obtained from previous steps.

   6. The data is retrieved from the API and stored in a pandas dataframe.

### 3. Data Analysis/Processing

- [In progress...] Data Analysis is done with LangChain, using the pandas dataframe agent. 

## Adding cubes

Currently, the cubes available to be queried by the chatbot are:

   - Consumer Price Index - CPI
   - dot_faf
   - Data_USA_Senate_election
   - Data_USA_President_election
   - Data_USA_House_election
   - [in progress] pums_5

In order to add cubes, the steps are:

   1. Add the cube to the tables.json file. The following fields must be filled:
      - name
      - api (Tesseract or Mondrian)
      - description
      - measures
            ```json
               {
                  "name": "Millions Of Dollars",
                  "description": "value in millions of dollars of a certain shipment."   
               }
            ```
      - variables
         - Add each level separately, filling the following fields for each:
            ```json
               {
                  "name": "State",
                  "description": "US states",
                  "parent dimension": "Geography",
                  "hierarchies": ["State", "County"]
               }
            ```

   2. Add the cube to the database (datausa_tables.cubes), filling the following columns (you can use the `cubes_to_db.py` script):
      - table_name
      - table_description
      - embedding (embedding of the table's description is represented as a 384-dimensional vector, derived using the `SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')` model)

   3. Add drilldown members & ids to the db (datausa_drilldowns.drilldowns)
      - This process can be initiated by executing the `drilldowns_to_db.py` script. During execution, the code will prompt for the API URL to fetch the drilldown members and IDs. Then, it will request the measure name in order to remove it from the dataframe before loading the data to the database.
      - The script then appends a column containing embeddings generated from the drilldown names using the same embedding model mentioned before.
      - This process needs to be repeated for each drilldown level within the cube or those required for making cuts. Time variables don't need to be loaded into the database.


# API beeing served by FastAPI

## How to run the api

On local development, you can run the following code:
```
uvicorn src.main:app --reload
```
## How to build the docker image
```
cd api/
docker build -t datausa-chat:<tag> .
```

## How to run the docker image
create a .env file with the required env variables
```
cd api/
docker run --env-file=./.env -p 80:80 datausa-chat:<tag>
```