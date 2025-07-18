import requests
import json
from sentence_transformers import SentenceTransformer
import spacy
import faiss
import numpy as np

import threading
import time

from collections import OrderedDict

from config import config,logger
if config["database"]["conn_type"] == "db_conn":
    from connect_vector_db import fetch_data_from_db_col #, fetch_data_from_db



class cache():

    timestamp = None
    conn_type = None

    model = None
    nlp = None

    hnsw_index = None
    prompt_dict = None


    def __init__(self):
        logger.info(f"cache creation start")

        self.timestamp = config['database']['first_timestamp']
        self.conn_type = config["database"]["conn_type"]

        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")

        self.prompt_dict = OrderedDict()
        self.create_hnsw_index()

        refresh_cache_thread = threading.Thread(target=self.refresh_cache, daemon=True)
        refresh_cache_thread.start()

        logger.info(f"cache creation end")



    def create_hnsw_index(self):
        # https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
        # In addition to the restrictions of the Flat index HNSW uses, HNSW does not support removing vectors from the index. This would destroy the graph structure.
        logger.info("HNSW index creation start")
        sample_embedding = self.model.encode(["Hello World!"]).astype(np.float32)
        logger.debug(f"embedding shape: {sample_embedding.shape}")
        dimension = sample_embedding.shape[1]
        self.hnsw_index = faiss.IndexHNSWFlat(dimension,32)
        self.hnsw_index.efConstruction = 200
        self.hnsw_index.efSearch = 50
        logger.info("HNSW index creation finished")

    def fetch_data(self):
        """Fetches prompt data from the chosen datastore and adds any new prompts to the index"""
        logger.info(f"fetching data from db using: {self.conn_type}")
        new_prompts = []

        if self.conn_type == "db_conn":
            new_prompts = self.fetch_data_db_conn()
        elif self.conn_type == "fastapi":
            new_prompts = self.fetch_data_fastapi()
        elif self. conn_type == "dummy":
            new_prompts = ["This is a dummy prompt", "Hello World!", "What", "Where", "Why"]

        for prompt in new_prompts.copy():
            if prompt not in self.prompt_dict:
                embeddings = self.model.encode([prompt]).astype(np.float32)
                self.prompt_dict[prompt] = embeddings
                self.hnsw_index.add(embeddings)
            else:
                logger.debug(f"duplicate prompt found: {prompt}")
                new_prompts.remove(prompt)

        logger.debug(f"new prompts added: {new_prompts}")


    def fetch_data_db_conn(self):
        """Fetches prompt data from the database connection datastore"""
        query = """
              SELECT prompt_txt
              FROM CERTIFIED_PROMPTS
            """
        cols = ["prompt"]
        df = fetch_data_from_db_col(query, cols)
        prompt_list = df["prompt"].tolist()
        logger.debug(f"prompt list length: {len(prompt_list)}")
        return prompt_list

    def fetch_data_fastapi(self):
        """Fetches prompt data from fastapi datastore"""
        try:
            url = f"{config['database']['url']}{config['database']['endpoint']}"
            params = {"previous_last_record_stamp": f"{self.timestamp}"}

            response = requests.get(url = url,params = params)

            logger.debug(vars(response))
            if response.status_code == 200:
                content = json.loads(response._content)
                logger.debug(content)

                self.timestamp = content["new_last_record_tstamp"]
                logger.info(f"new timestamp: {self.timestamp}")

                new_prompts = content["prompts"]
                logger.info(f"new prompts: {new_prompts}")

                if response._next is not None:
                    logger.warning("next page detected but not implemented yet")

                return new_prompts

            else:
                logger.debug(f"request: {vars(response.request)}")
                logger.debug(f"response: {vars(response)}")
                return []
        except Exception as e:
            logger.error(f"error getting data from database: {e}")
            return []


    def refresh_cache(self):
        logger.debug(f"Refresh cache thread started: {threading.current_thread().ident}")
        while True:
            logger.debug(f"refreshing cache start: {time.localtime()}")
            self.fetch_data()
            logger.debug(f"refreshing cache finished: {time.localtime()}")
            time.sleep(config["database"]["refresh_time"])


    def semantic_search(self, query, top_k=3):
        """Perform semantic search using the HNSW index."""

        # Encode the query and ensure it's float32
        logger.debug(f"model type: {type(self.model.encode([query]))}")
        logger.debug("*****debug1****")
        query_embedding = self.model.encode([query]).astype(np.float32)

        # Check if the query embedding is valid
        if query_embedding is None or query_embedding.size == 0:
            logger.warning("Query embedding is empty or invalid.")
            return []

        # Perform the FAISS search
        try:
            distances, indices = self.hnsw_index.search(query_embedding, top_k)
        except Exception as e:
            logger.error(f"Error during FAISS search: {e}")
            return []

        # Debug print statements
        logger.debug(f"Distances: {distances}")
        logger.debug(f"Indices: {indices}")

        # Check if distances or indices are None or have an unexpected shape
        if indices is None or distances is None:
            logger.warning("FAISS search returned None.")
            return []

        if len(indices) == 0 or len(distances) == 0:
            logger.warning("FAISS search returned empty results.")
            return []

        # Check the shape of the returned arrays
        if len(indices[0]) == 0 or len(distances[0]) == 0:
            logger.warning("FAISS search returned empty lists.")
            return []

        # Ensure indices[0] and distances[0] are not empty
        if not isinstance(indices[0], np.ndarray) or not isinstance(distances[0], np.ndarray):
            logger.warning("FAISS search returned unexpected types.")
            return []


        #def get_similar_prompts(self, query_embedding, k=10):
            #distances, indices = self.faiss_index.search(np.array([query_embedding]), k)
            #return [list(self.cache.keys())[i] for i in indices[0]]

        # Construct the results safely
        results = []
        logger.debug(f"number of prompts: {len(self.prompt_dict)}")
        for i, idx in enumerate(indices[0]):
            logger.debug(f"i: {i}, idx: {idx}")
            if idx < len(self.prompt_dict):
                results.append((list(self.prompt_dict.keys())[idx], distances[0][i]))
            else:
                logger.warning(f"Index {idx} is out of bounds for prompt_list.")
        logger.debug("*****debug2**** **")


        return results



    def perform_ner(self,text):
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return entities

    def process_results(self,results):
        processed_results = []
        for result in results:
            entities = self.perform_ner(result)
            processed_results.append({
                "text": result,
                "entities": entities
            })
        return processed_results