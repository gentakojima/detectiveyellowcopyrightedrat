import json
import logging
import configparser
import types
from os.path import expanduser
import pymysql.cursors
from pymysql.err import InterfaceError, IntegrityError

configdir = expanduser("~") + "/.config/detectivepikachu"
configfile = configdir + "/config.ini"

config = configparser.ConfigParser()
config.read(configfile)

db = None

def refreshDb():
    global db
    try:
        db = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
        logging.debug("Connected to database")
    except:
        print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
        logging.debug("Can't connect to database!")

def saveGroup(group):
    global db
    logging.debug("storagemethods:saveSpreadsheet: %s" % (group))
    if "settings_message" not in group.keys():
        group["settings_message"] = None
    if "alerts" not in group.keys():
        group["alerts"] = 1
    if "disaggregated" not in group.keys():
        group["disaggregated"] = 0
    if "latebutton" not in group.keys():
        group["latebutton"] = 0
    if "refloat" not in group.keys():
        group["refloat"] = 0
    if "candelete" not in group.keys():
        group["candelete"] = 1
    if "gotitbuttons" not in group.keys():
        group["gotitbuttons"] = 0
    with db.cursor() as cursor:
        sql = "INSERT INTO grupos (id, title, spreadsheet) VALUES (%s, %s, %s) \
        ON DUPLICATE KEY UPDATE title = %s, spreadsheet = %s, settings_message = %s, alerts = %s, disaggregated = %s, latebutton = %s, refloat = %s, candelete = %s, gotitbuttons = %s;"
        cursor.execute(sql, (group["id"], group["title"], group["spreadsheet"], group["title"], group["spreadsheet"], group["settings_message"], group["alerts"], group["disaggregated"], group["latebutton"], group["refloat"], group["candelete"], group["gotitbuttons"]))
    db.commit()

def getGroup(group_id):
    global db
    logging.debug("storagemethods:getGroup: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`title`,`spreadsheet`,`testgroup`,`alerts`,`disaggregated`,`settings_message`,`latebutton`,`refloat`,`candelete`,`gotitbuttons` FROM `grupos` WHERE `id`=%s"
        cursor.execute(sql, (group_id))
        result = cursor.fetchone()
        return result

def getGroupsByUser(user_id):
    global db
    logging.debug("storagemethods:getGroupsByUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `grupos`.`id` as `id`,`title`,`spreadsheet`,`testgroup`,`alerts`,`disaggregated`,`latebutton`,`refloat`,`candelete`,`gotitbuttons` FROM `grupos` \
        LEFT JOIN incursiones ON incursiones.grupo_id = grupos.id \
        RIGHT JOIN voy ON voy.incursion_id = incursiones.id \
        WHERE voy.usuario_id = %s \
		GROUP BY grupos.id"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
        return result

def savePlaces(group_id, places):
    global db
    logging.debug("storagemethods:savePlaces: %s %s" % (group_id, places))
    with db.cursor() as cursor:
        params_vars = []
        params_replacements = [group_id]
        for place in places:
            params_vars.append("%s")
            params_replacements.append(place["desc"])
        sql = "UPDATE incursiones SET gimnasio_id=NULL WHERE grupo_id=%s AND gimnasio_text NOT IN ("+(",".join(params_vars))+")"
        cursor.execute(sql, params_replacements)
        sql = "DELETE alertas, gimnasios FROM gimnasios LEFT JOIN alertas ON alertas.gimnasio_id = gimnasios.id WHERE gimnasios.grupo_id=%s AND gimnasios.name NOT IN ("+(",".join(params_vars))+")"
        cursor.execute(sql, params_replacements)
        for place in places:
            try:
                sql = "INSERT INTO gimnasios (grupo_id,name,latitude,longitude,keywords) \
                VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE latitude=%s, longitude=%s, keywords=%s;"
                cursor.execute(sql, (group_id, place["desc"], place["latitude"], place["longitude"], json.dumps(place["names"]), place["latitude"], place["longitude"], json.dumps(place["names"])))
            except IntegrityError:
                db.rollback()
                return False
    db.commit()
    return True

def getAlerts(user_id):
    global db
    logging.debug("storagemethods:getAlerts: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`usuario_id`,`gimnasio_id` FROM `alertas` WHERE `usuario_id`=%s"
        cursor.execute(sql, (user_id))
        alerts = []
        for row in cursor:
            alerts.append({"id":row["id"], "user_id":row["usuario_id"], "place_id":row["gimnasio_id"]})
        return alerts

def getAlertsByPlace(place_id):
    global db
    logging.debug("storagemethods:getAlertsByPlace: %s" % (place_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`usuario_id`,`gimnasio_id` FROM `alertas` WHERE `gimnasio_id`=%s"
        cursor.execute(sql, (place_id))
        alerts = []
        for row in cursor:
            alerts.append({"id":row["id"], "user_id":row["usuario_id"], "place_id":row["gimnasio_id"]})
        return alerts

def addAlert(user_id, place_id):
    global db
    logging.debug("storagemethods:addAlert: %s %s" % (user_id, place_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `alertas` WHERE `usuario_id` = %s AND `gimnasio_id` = %s"
        cursor.execute(sql, (user_id, place_id))
        result = cursor.fetchone()
        if result != None:
            return False
        sql = "INSERT INTO alertas (usuario_id, gimnasio_id) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, place_id))
    db.commit()
    return True

def delAlert(user_id, place_id):
    global db
    logging.debug("storagemethods:delAlert: %s %s" % (user_id, place_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `alertas` WHERE `usuario_id` = %s AND `gimnasio_id` = %s"
        cursor.execute(sql, (user_id, place_id))
        result = cursor.fetchone()
        if result == None:
            return False
        sql = "DELETE FROM alertas WHERE `usuario_id`=%s and `gimnasio_id`=%s"
        cursor.execute(sql, (user_id, place_id))
    db.commit()
    return True

def clearAlerts(user_id):
    global db
    logging.debug("storagemethods:clearAlerts: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `alertas` WHERE `usuario_id` = %s"
        cursor.execute(sql, (user_id))
        result = cursor.fetchone()
        if result == None:
            return False
        sql = "DELETE FROM alertas WHERE `usuario_id`=%s"
        cursor.execute(sql, (user_id))
    db.commit()
    return True

def getPlaces(group_id, ordering="name"):
    global db
    logging.debug("storagemethods:getPlaces: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`latitude`,`longitude`,`keywords` FROM `gimnasios` WHERE `grupo_id`=%s"
        if ordering == "name":
            sql = sql + " ORDER BY name"
        elif ordering == "id":
            sql = sql + " ORDER BY id"
        cursor.execute(sql, (group_id))
        gyms = []
        for row in cursor:
            gyms.append({"id":row["id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"])})
        return gyms

def getPlace(id):
    global db
    logging.debug("storagemethods:getPlace: %s" % (id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`grupo_id`,`latitude`,`longitude`,`keywords` FROM `gimnasios` WHERE `id`=%s"
        cursor.execute(sql, (id))
        for row in cursor:
            return {"id":row["id"], "group_id":row["grupo_id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"])}
        return None

def getPlacesByLocation(latitude, longitude, distance=100):
    global db
    logging.debug("storagemethods:getPlacesByLocation: %s %s %s" % (latitude, longitude, distance))
    d = float(distance)/50000.0
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`,`latitude`,`longitude`,`name` FROM `gimnasios` WHERE `latitude`> %s AND `latitude` < %s AND `longitude` > %s and `longitude` < %s"
        cursor.execute(sql, (float(latitude)-d,float(latitude)+d,float(longitude)-d,float(longitude)+d))
        result = cursor.fetchall()
        return result

def saveUser(user):
    global db
    logging.debug("storagemethods:saveUser: %s" % (user))
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

def refreshUsername(user_id, username):
    global db
    logging.debug("storagemethods:refreshUsername: %s %s" % (user_id, username))
    thisuser = getUser(user_id)
    if thisuser == None:
        thisuser = {}
        thisuser["id"] = user_id
    if username != None and username != "None":
        thisuser["username"] = username
    saveUser(thisuser)
    return thisuser

def getUser(user_id, reconnect=True):
    global db
    logging.debug("storagemethods:getUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username` FROM `usuarios` WHERE `id`=%s"
        try:
            cursor.execute(sql, (user_id))
        except InterfaceError:
            if reconnect == True:
                logging.info("Error interfacing with the database! Trying to reconnect...")
                refreshDb()
                getUser(user_id, False)
            else:
                logging.info("Error interfacing with the database but already tried to reconnect")
                raise
        result = cursor.fetchone()
        return result

def saveRaid(raid):
    global db
    logging.debug("storagemethods:saveRaid: %s" % (raid))
    if "gimnasio_id" not in raid.keys():
        raid["gimnasio_id"] = None
    if "endtime" not in raid.keys():
        raid["endtime"] = None
    if "id" not in raid.keys():
        with db.cursor() as cursor:
            sql = "SELECT id FROM grupos WHERE id=%s"
            cursor.execute(sql, (raid["grupo_id"]))
            result = cursor.fetchone()
            if result == None:
                sql = "INSERT INTO grupos (`id`) VALUES (%s);"
                cursor.execute(sql, (raid["grupo_id"]))
            sql = "INSERT INTO incursiones (`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `endtime`, `gimnasio_id`, `gimnasio_text` ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(sql, (raid["grupo_id"], raid["usuario_id"], raid["message"], raid["pokemon"], raid["time"], raid["endtime"], raid["gimnasio_id"], raid["gimnasio_text"]))
            db.commit()
            return cursor.lastrowid
    else:
        with db.cursor() as cursor:
            sql = "UPDATE incursiones SET `pokemon`=%s, `time`=%s, `endtime`=%s, `gimnasio_id`=%s, `gimnasio_text`=%s, edited=1, message=%s WHERE id=%s;"
            cursor.execute(sql, (raid["pokemon"], raid["time"], raid["endtime"], raid["gimnasio_id"], raid["gimnasio_text"], raid["message"], raid["id"]))
            db.commit()
            return raid["id"]

def getRaid(raid_id):
    global db
    logging.debug("storagemethods:getRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `endtime`, `gimnasio_id`, `gimnasio_text`, `edited`, `cancelled`, `addedtime`, `ended` FROM `incursiones` WHERE `id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
        return result

def getRaidPeople(raid_id):
    global db
    logging.debug("storagemethods:getRaidPeople: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username`, `plus`, `estoy`, `tarde`, `level`, `team`, `lotengo` FROM `incursiones` \
        LEFT JOIN `voy` ON `voy`.`incursion_id` = `incursiones`.`id` \
        LEFT JOIN `usuarios` ON `usuarios`.`id` = `voy`.`usuario_id` WHERE `incursiones`.`id`=%s \
        ORDER BY `voy`.`addedtime` ASC"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchall()
        if result[0]["id"] == None:
            return None
        else:
            return result

def getRaidbyMessage(grupo_id, message_id):
    global db
    logging.debug("storagemethods:getRaidByMessage: %s %s" % (grupo_id, message_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `endtime`, `gimnasio_id`, `gimnasio_text`, `edited`, `cancelled`, `addedtime`, `ended` FROM `incursiones` WHERE  grupo_id = %s and `message` = %s"
        cursor.execute(sql, (grupo_id, message_id))
        result = cursor.fetchone()
        return result

def getLastRaids(grupo_id, number):
    global db
    logging.debug("storagemethods:getlastRaids: %s %s" % (grupo_id, number))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `time`, `endtime`, `gimnasio_id`, `gimnasio_text`, `edited`, `cancelled`, `addedtime`, `ended` FROM `incursiones` WHERE  grupo_id = %s ORDER BY `addedtime` DESC LIMIT 0,%s"
        cursor.execute(sql, (grupo_id, number))
        result = cursor.fetchall()
        if result[0]["id"] == None:
            return None
        else:
            return result

def getCreadorRaid(raid_id):
    global db
    logging.debug("storagemethods:getCreadorRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username` FROM `incursiones` LEFT JOIN `usuarios` ON `usuarios`.`id` = `incursiones`.`usuario_id` WHERE `incursiones`.`id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
        return result

def raidVoy(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidVoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id) VALUES (%s, %s)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET plus = 0, estoy = 0, tarde = 0, lotengo = NULL WHERE incursion_id=%s and usuario_id=%s"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidNovoy(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidNovoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "DELETE FROM voy WHERE `incursion_id`=%s and usuario_id=%s;"
        cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidPlus1(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidPlus1: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
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

def raidEstoy(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidEstoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy) VALUES (%s, %s, 1)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET estoy=1, tarde=0 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidLlegotarde(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidLlegotarde: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, tarde) VALUES (%s, %s, 1)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET tarde=1, estoy=0 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidLotengo(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidLotengo: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy, lotengo) VALUES (%s, %s, 1, 1)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET tarde=0, estoy=1, lotengo = 1 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def raidEscapou(grupo_id, message_id, user_id):
    global db
    logging.debug("storagemethods:raidEscapou: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid["ended"] == 1:
            return False
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy, lotengo) VALUES (%s, %s, 1, 0)"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET tarde=0, estoy=1, lotengo = 0 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    return True

def deleteRaid(raid_id):
    global db
    logging.debug("storagemethods:deleteRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "DELETE FROM voy WHERE `incursion_id`=%s;"
        cursor.execute(sql, (raid_id))
        sql = "DELETE FROM incursiones WHERE `id`=%s;"
        cursor.execute(sql, (raid_id))
    db.commit()
    return True

def cancelRaid(raid_id):
    global db
    logging.debug("storagemethods:cancelRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        raid = getRaid(raid_id)
        if raid["cancelled"] == 1:
            return False
        else:
            sql = "UPDATE incursiones SET `cancelled`=1 WHERE id=%s;"
            cursor.execute(sql, (raid_id))
            db.commit()
    return True

def endOldRaids():
    global db
    logging.debug("storagemethods:endOldRaids")
    with db.cursor() as cursor:
        try:
            sql = "SELECT `id` FROM `incursiones` WHERE addedtime < (NOW() - INTERVAL 3 HOUR) AND ended = 0 AND pokemon NOT IN ('Mewtwo', 'Ho-Oh') LIMIT 0,10"
            cursor.execute(sql)
            result1 = cursor.fetchall()
            sql = "SELECT `id` FROM `incursiones` WHERE addedtime < (NOW() - INTERVAL 5 DAY) AND ended = 0 AND pokemon IN ('Mewtwo', 'Ho-Oh') LIMIT 0,10"
            cursor.execute(sql)
            result2 = cursor.fetchall()
            if isinstance(result1,list) and isinstance(result2,list):
                results = result1 + result2
            elif isinstance(result1,list):
                results = result1
            elif isinstance(result2,list):
                results = result2
            else:
                results = []
            for r in results:
                if r["id"] != None:
                    sql = "UPDATE incursiones SET `ended`=1 WHERE id=%s;"
                    cursor.execute(sql, (r["id"]))
            db.commit()
            return results
        except:
            refreshDb()
            return []
