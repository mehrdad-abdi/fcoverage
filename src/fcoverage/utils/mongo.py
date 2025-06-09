from typing import Any, Dict, List
from pymongo import MongoClient


class MongoDBHelper:
    def __init__(
        self,
        connection_string: str,
        database: str,
        collection: str,
    ):
        self.client = MongoClient(connection_string)
        self.db = self.client[database]
        self.collection = self.db[collection]

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[Any]:
        result = self.collection.insert_many(documents)
        return result.inserted_ids

    def ids(self):
        return {doc["_id"] for doc in self.collection.find({}, {"_id": 1})}

    def find_list(self, query: Dict[str, Any]):
        return self.collection.find(query)

    def sync_documents(self, documents: List[Dict[str, Any]]):
        current_ids = {d["id"] for d in documents}

        # 1. Get all existing IDs from the DB
        existing_ids = self.ids()

        # 2. Identify what to delete and what to add
        ids_to_add = [id_ for id_ in current_ids if id_ not in existing_ids]
        ids_to_delete = [id_ for id_ in existing_ids if id_ not in current_ids]

        # 3. Delete obsolete entries
        if ids_to_delete:
            for id in ids_to_delete:
                self.collection.delete_one(ids=id)

        # 4. Add new entries
        if ids_to_add:
            docs_to_add = [doc for doc in documents if doc["id"] in ids_to_add]
            self.add_documents(docs_to_add)
