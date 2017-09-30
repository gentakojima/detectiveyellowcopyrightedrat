import json
import logging

def saveSpreadsheet(group_id, spreadsheet, db):
    logging.debug("storagemethods:saveSpreadsheet: %s %s %s" % (group_id, spreadsheet, db))
    with db.cursor() as cursor:
        sql = "INSERT INTO grupos (id,spreadsheet) VALUES (%s, %s) \
        ON DUPLICATE KEY UPDATE spreadsheet = %s;"
        cursor.execute(sql, (group_id, spreadsheet, spreadsheet))
    db.commit()

def savePlaces(group_id, places, db):
    logging.debug("storagemethods:savePlaces: %s %s %s" % (group_id, places, db))
    with db.cursor() as cursor:
        sql = "DELETE FROM gimnasios WHERE grupo_id=%s;"
        cursor.execute(sql, (group_id))
        for place in places:
            sql = "INSERT INTO gimnasios (grupo_id,name,latitude,longitude,keywords) \
            VALUES (%s, %s, %s, %s, %s);"
            cursor.execute(sql, (group_id, place["desc"], place["latitude"],place["longitude"],json.dumps(place["names"])))
    db.commit()

def getSpreadsheet(group_id, db):
    logging.debug("storagemethods:getSpreadsheet: %s %s" % (group_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `spreadsheet` FROM `grupos` WHERE `id`=%s"
        cursor.execute(sql, (group_id))
        result = cursor.fetchone()
        if result != None:
            return result["spreadsheet"]
        else:
            return None

def getPlaces(group_id, db):
    logging.debug("storagemethods:getPlaces: %s %s" % (group_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`latitude`,`longitude`,`keywords` FROM `gimnasios` WHERE `grupo_id`=%s"
        cursor.execute(sql, (group_id))
        gyms = []
        for row in cursor:
            gyms.append({"id":row["id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"])})
        return gyms

def getPlace(id, db):
    logging.debug("storagemethods:getPlace: %s %s" % (id, db))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`latitude`,`longitude`,`keywords` FROM `gimnasios` WHERE `id`=%s"
        cursor.execute(sql, (id))
        for row in cursor:
            return {"id":row["id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"])}
        return None

def saveUser(user, db):
    logging.debug("storagemethods:saveUser: %s %s" % (user, db))
    with db.cursor() as cursor:
        sql = "INSERT INTO usuarios (id,level,team,username) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE level=%s, team=%s, username=%s;"
        if "level" not in user.keys():
            user["level"] = None
        if "team" not in user.keys():
            user["team"] = None
        if "username" not in user.keys():
            user["username"] = None
        cursor.execute(sql, (user["id"], user["level"], user["team"], user["username"], user["level"], user["team"], user["username"]))
    db.commit()

def refreshUsername(user_id, username, db):
    logging.debug("storagemethods:refreshUsername: %s %s %s" % (user_id, username, db))
    thisuser = getUser(user_id, db)
    if thisuser == None:
        thisuser = {}
        thisuser["id"] = user_id
    if username != None and username != "None":
        thisuser["username"] = username
    saveUser(thisuser, db)
    return thisuser

def getUser(user_id, db):
    logging.debug("storagemethods:getUser: %s %s" % (user_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username` FROM `usuarios` WHERE `id`=%s"
        cursor.execute(sql, (user_id))
        result = cursor.fetchone()
        return result

def saveRaid(raid, db):
    logging.debug("storagemethods:saveRaid: %s %s" % (raid, db))
    if "gimnasio_id" not in raid.keys():
        raid["gimnasio_id"] = None
    if "id" not in raid.keys():
        with db.cursor() as cursor:
            sql = "INSERT INTO incursiones (`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `gimnasio_id`, `gimnasio_text` ) VALUES (%s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(sql, (raid["grupo_id"], raid["usuario_id"], raid["message"], raid["pokemon"], raid["time"], raid["gimnasio_id"], raid["gimnasio_text"]))
            db.commit()
            return cursor.lastrowid
    else:
        with db.cursor() as cursor:
            sql = "UPDATE incursiones SET `pokemon`=%s, `time`=%s, `gimnasio_id`=%s, `gimnasio_text`=%s, edited=1 WHERE id=%s;"
            cursor.execute(sql, (raid["pokemon"], raid["time"], raid["gimnasio_id"], raid["gimnasio_text"], raid["id"]))
            db.commit()
            return raid["id"]

def getRaid(raid_id, db):
    logging.debug("storagemethods:getRaid: %s %s" % (raid_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `gimnasio_id`, `gimnasio_text`, `edited` FROM `incursiones` WHERE `id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
        return result

def getRaidPeople(raid_id, db):
    logging.debug("storagemethods:getRaidPeople: %s %s" % (raid_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username`, `plus`, `estoy`, `level`, `team` FROM `incursiones` \
        LEFT JOIN `voy` ON `voy`.`incursion_id` = `incursiones`.`id` \
        LEFT JOIN `usuarios` ON `usuarios`.`id` = `voy`.`usuario_id` WHERE `incursiones`.`id`=%s \
        ORDER BY `addedtime` ASC"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchall()
        if result[0]["id"] == None:
            return None
        else:
            return result

def getRaidbyMessage(grupo_id, message_id, db):
    logging.debug("storagemethods:getRaidByMessage: %s %s %s" % (grupo_id, message_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `gimnasio_id`, `gimnasio_text`, `edited` FROM `incursiones` WHERE  grupo_id = %s and `message` = %s"
        cursor.execute(sql, (grupo_id, message_id))
        result = cursor.fetchone()
        return result

def getCreadorRaid(raid_id, db):
    logging.debug("storagemethods:getCreadorRaid: %s %s" % (raid_id, db))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username` FROM `incursiones` LEFT JOIN `usuarios` ON `usuarios`.`id` = `incursiones`.`usuario_id` WHERE `incursiones`.`id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
        return result

def raidVoy(grupo_id, message_id, user_id, db):
    logging.debug("storagemethods:raidVoy: %s %s %s %s" % (grupo_id, message_id, user_id, db))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id, db)
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id) VALUES (%s, %s)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET plus = 0, estoy = 0 WHERE incursion_id=%s and usuario_id=%s"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidNovoy(grupo_id, message_id, user_id, db):
    logging.debug("storagemethods:raidNovoy: %s %s %s %s" % (grupo_id, message_id, user_id, db))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id, db)
        sql = "DELETE FROM voy WHERE `incursion_id`=%s and usuario_id=%s;"
        cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidPlus1(grupo_id, message_id, user_id, db):
    logging.debug("storagemethods:raidPlus1: %s %s %s %s" % (grupo_id, message_id, user_id, db))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id, db)
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result != None:
            if result["plus"]>5:
                return False
            sql = "UPDATE voy SET plus=plus+1 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            result = {"plus":0}
            sql = "INSERT IGNORE INTO voy (incursion_id, usuario_id, plus) VALUES (%s, %s, 1)"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return result["plus"]+1

def raidEstoy(grupo_id, message_id, user_id, db):
    logging.debug("storagemethods:raidEstoy: %s %s %s %s" % (grupo_id, message_id, user_id, db))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id, db)
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy) VALUES (%s, %s, 1)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET estoy=1 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def deleteRaid(raid_id, db):
    logging.debug("storagemethods:deleteRaid: %s %s" % (raid_id, db))
    with db.cursor() as cursor:
        sql = "DELETE FROM voy WHERE `incursion_id`=%s;"
        cursor.execute(sql, (raid_id))
        sql = "DELETE FROM incursiones WHERE `id`=%s;"
        cursor.execute(sql, (raid_id))
    db.commit()
    return True
