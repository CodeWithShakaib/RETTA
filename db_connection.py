import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = myclient["REETA_database"]