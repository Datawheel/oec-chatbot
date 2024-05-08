# OEC-chat

This repository contains scripts for a chatbot that leverages artificial intelligence to interact with users and gather insights from [oec.world](https://https://oec.world/). The chatbot aims to deliver meaningful insights directly from natural language queries, simplifying the process for users to access and analyze data.

## Folders inside **`api/`**

### 1. **`data/`**
   - Contains JSON files featuring few-shot examples tailored for the Language Model (LLM). 

   - Also contains `schema.json` which contains available cubes, with their descriptions, column names, and relevant details.

### 2. **`setup/`**
   - Stores all the scripts used to extract the schema and ingest the cubes and drilldowns into a database.

### 3. **`src/`**
   - Houses all the main scripts to run the chatbot.
  
   - **Subfolders:**
     1. **`api_data_request/`**
        - Core scripts responsible for constructing the API URL. Contains functions for processing query cuts and matching values with their respective IDs.
        - Stores de ApiBuilder class.

     2. **`data_analysis/`**
        - Contains scripts used for data analysis (mainly using [LangChain](https://python.langchain.com/docs/get_started/introduction)).

     3. **`table_selection/`**
        - All scripts needed to lookup and manage the relevant cube that contains the data needed to answer the user's query.

     4. **`utils/`**
        - Stores preprocessing, logs and similarity search scripts. Also stores the SQL similarity functions needed for the similarity search.

     5. **`wrapper/`**
        - Contains the scripts that power the wrapper of the chat.


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
        "drilldowns": ["Origin State", "Destination State"],
        "measures": ["Thousands Of Tons"],
        "filters": ["Year = 2020", "SCTG2 = Coal", "Origin State = New York", "Destination State = California"]
     }
```

   3. Extracts the JSON from the LM's output string.

   4. Instantiates an ApiBuilder object and sets the variables, measures, and cuts provided by the LLM as attributes using the class methods.

   4. For the cuts, a similarity search is done over the corresponding dimension members of the cube to extract their ids from the database (with the `cuts_processing()` function).

   5. The API URL (for Mondrian or Tesseract) is built using the processed cuts, drilldowns and measures obtained from previous steps by running the `build_api()` method.

   6. The data is retrieved from the API using the `fetch_data()` method and stored in a pandas dataframe.


### 3. Data Analysis/Processing

- Data Analysis is done with LangChain, using the pandas dataframe agent. The Agent receives the dataframe, the user's question and the API endpoint used to retrieve the data and returns an answer back. 

## Adding cubes

Currently, the cubes available to be queried by the chatbot are:

   - trade_i_baci_a_96
   - trade_i_baci_a_22
   - trade_s_rus_m_hs
   - tariffs_i_wits_a_hs_new
   - trade_s_esp_m_hs
   - trade_unit_value_96
   - complexity_eci_multidimensional
   - complexity_pci_a_hs96_hs6
   - complexity_pci_a_hs22_hs6
   - complexity_pci_a_hs96_hs4
   - complexity_pci_a_hs22_hs4
   - services_i_comtrade_a_eb02
   - trade_i_oec_a_sitc2
   - complexity_eci_a_hs96_hs6
   - complexity_eci_a_hs22_hs6
   - complexity_eci_a_hs96_hs4
   - complexity_eci_a_hs22_hs4
   - indicators_i_wdi_a
   - gini_inequality_income

In order to add a new cube, the steps are:

   1. Ensure the new cube is in the `schema.json` file. 

   2. Add the name of the new cube to the include_cubes list in the `load_cubes_to_db.py` script and run it. This will ingest the cube, along with its' description and embedding, to the **chat.cubes** table in the database.
      - If include_cubes is set to False, it will ingest all the cubes found in `schema.json`.

   3. Add drilldown members & ids to the db (**chat.drilldowns**)
      - This process can be initiated by executing the `load_drilldowns_to_db.py` script. 
      - Add the name of the new cube to the include_cubes list and run the script.
      - Same as before, if include_cubes is set to False, it will ingest all the drilldowns of cubes found in `schema.json`.

### [For future projects] In progress...

To add all the cubes of a project automatically, they can be mapped from the tesseract cubes endpoint to the custom format needed in the app. To do this follow these steps:

   1. Run `schema_to_json.py`. This will map the tesseract cubes endpoint to `schema.json`.

   2. Run `load_cubes_to_db.py`.

   3. Run `load_drilldowns_to_db.py`.

# API beeing served by FastAPI

## How to run the api

On local development, you can run the following code:
```
uvicorn main:app --reload
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

## Python Eslint Configuration
- [https://code.visualstudio.com/docs/python/formatting](https://code.visualstudio.com/docs/python/formatting)
- [https://docs.astral.sh/ruff/configuration/](https://docs.astral.sh/ruff/configuration/)