#############################
#                           #
#       CONFIG FILE         #
#                           #
#############################


# ---------- API SETTINGS
groupToken = "token" # vk group token
debugStatus = True # debug status

# ---------- FD SETTINGS
fd = [''] # full rights
isLogEnabled = False


# ---------- SQLITE SETTINGS
creationQuery = """CREATE TABLE IF NOT EXISTS users(
                vk INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                balance INTEGER NOT NULL DEFAULT 1,
                isAdmin INTEGER NOT NULL DEFAULT 0,
                isHelper INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS blacklist(
                vk INTEGER NOT NULL)
                """ # default database creation query