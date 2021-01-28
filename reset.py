from util.database import datapack_db
DB = datapack_db()
DB.reset()
DB.cur.execute('use datapack_collection;')
DB.reset()