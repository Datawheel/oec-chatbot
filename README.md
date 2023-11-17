# datausa-chat

This repository contains scripts for a chatbot that leverages artificial intelligence to interact with users and gather insights from [DataUSA.io](https://datausa.io/). The chatbot aims to deliver meaningful insights directly from natural language queries, simplifying the process for users to access and analyze data.

## Folders inside **`api/`**

### 1. **`data/`**
   - Contains JSON files featuring few-shot examples tailored for the Language Model (LLM). Additionally, includes a file detailing available cubes, with their descriptions, column names, and relevant details.

### 2. **`utils/`**
   - Houses all the main scripts to run the chatbot.
  
   - **Subfolders:**
     1. **`api_data_request/`**
        - Core scripts responsible for constructing the API URL. Contains functions for processing query cuts and matching values with their respective IDs.
     
     2. **`preprocessors/`**
        - Contains scripts that preprocess text (or any other data type as needed).

     3. **`table_selection/`**
        - All scripts needed to lookup the relevant table/cube that contains the data needed to answer a user's query.



## General Workflow

### 1. Table Selection

1. Matches the user's Natural Language Query (NLQ) to the table that *should* contain the relevant data to give an answer. To achieve this there are 3 options:

   - **Option 1: get_relevant_tables_from_database()**
     - Utilizes embeddings to match the query with the tables' descriptions in the database using an SQL similarity function.

   - **Option 2: get_relevant_tables_from_LM()**
     - Provides the Language Model (LM) with the names and descriptions of all available tables and asks the LM to choose one.

   - **Option 3: request_tables_to_lm_from_db()**
     - Hybrid approach that obtains the top N matches from the database using embeddings. It then asks the LM to choose between these N tables.

2. All the above functions return the name of the most relevant table.

### 2. API URL Generator & Data Request

   1. Builds a prompt that includes the table to query (with its description and column names) and the NLQ given by the user.

   2. Requests the Language Model (LM) to return a comment explaining why the chosen variables, measures, and filters can answer the query, along with a JSON containing these parameters with the following structure:


```json
     {
        "variables": ["Origin State", "Destination State"],
        "measures": ["Thousands Of Tons"],
        "filters": ["Year = 2020", "SCTG2 = Coal", "Origin State = New York", "Destination State = California"]
     }
```


   3. Extracts the JSON from the LM's output string.

   4. For the cuts, a similarity search is done over the corresponding dimension members to extract its' id.

   5. The API URL (for Mondrian or Tesseract) is built using the processed cuts, drilldowns and measures obtained from previous steps.

   6. The data is retrieved from the API and stored in a pandas dataframe.

### 3. Data Analysis/Processing

- To be continued...
