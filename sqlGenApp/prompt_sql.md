### Task
Generate a SQL query to answer [QUESTION]{user_question}[/QUESTION]

### Instructions
- If you cannot answer the question with the available database schema, return 'I do not know'
- In a join query with 2 or more tables, make sure that column names used in the query are qualified fully by table name prefix. For example, table_name.column_name. 
- Never use aliases for table names. 
- Double check that a column name belongs to the table whose prefix is used for a given column.
- If the question says 'show tables' or 'show names of the tables' then return a list of names of tables in the schema

### Database Schema
The query will run on a database with the following schema:
{table_metadata_string}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{user_question}[/QUESTION]
[SQL]
