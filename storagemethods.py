# Detective Yellowcopyrightedrat - A Telegram bot to organize Pokémon GO raids
# Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import types
import pymysql.cursors
from pymysql.err import InterfaceError, IntegrityError
from datetime import datetime, timedelta
from pytz import timezone
import time
import threading
from config import config

def getDbConnection():
    try:
        globaldb = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
        logging.debug("Connected to database from thread %s " % threading.get_ident())
    except:
        print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
        logging.debug("Can't connect to database!")
    return globaldb

# dbconnections = []
# def getDbConnection():
#     global dbconnections
#     for i in range(0,len(dbconnections)):
#         if dbconnections[i]["thread_id"] == threading.get_ident():
#             try:
#                 logging.debug("DATABASE: Trying to reuse connection from thread %s " % threading.get_ident())
#                 dbconnections[i]["c"].ping()
#                 return dbconnections[i]["c"]
#             except:
#                 logging.debug("DATABASE: Reconnecting from thread %s " % threading.get_ident())
#                 dbconnections[i]["c"] = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
#                 return dbconnections[i]["c"]
#     try:
#         logging.debug("DATABASE: Creating new database connection from thread %s " % threading.get_ident())
#         conn = pymysql.connect(host=config["database"]["host"], user=config["database"]["user"], password=config["database"]["password"], db=config["database"]["schema"], charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
#         dbconnections.append({"thread_id": threading.get_ident(), "c": conn})
#     except:
#         print("No se puede conectar a la base de datos.\nComprueba el fichero de configuración!")
#         logging.debug("Can't connect to database!")
#     return conn

def searchTimezone(tz):
    db = getDbConnection()
    logging.debug("storagemethods:searchTimezone: %s" % (tz))
    with db.cursor() as cursor:
        sql = "SELECT `Name` as `name` FROM `mysql`.`time_zone_name` WHERE Name NOT LIKE %s AND Name NOT LIKE %s AND Name LIKE %s"
        cursor.execute(sql, ("posix%", "right%", "%"+tz+"%"))
        result = cursor.fetchone()
    db.close()
    return result

def saveGroup(group):
    db = getDbConnection()
    logging.debug("storagemethods:saveSpreadsheet: %s" % (group))
    if "timezone" not in group.keys():
        group["timezone"] = "Europe/Madrid"
    for k in ["settings_message","spreadsheet","talkgroup","alias"]:
        if k not in group.keys():
            group[k] = None
    for k in ["disaggregated","latebutton","refloat","gotitbuttons","gymcommand","babysitter","timeformat","icontheme","refloatauto"]:
        if k not in group.keys():
            group[k] = 0
    for k in ["alerts","candelete","locations","raidcommand"]:
        if k not in group.keys():
            group[k] = 1
    if "plusmax" not in group.keys():
        group["plusmax"] = 5
    with db.cursor() as cursor:
        sql = "INSERT INTO grupos (id, title, alias, spreadsheet) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE title = %s, alias = %s, spreadsheet = %s, settings_message = %s, alerts = %s, disaggregated = %s, latebutton = %s, refloat = %s, candelete = %s, gotitbuttons = %s, locations = %s, gymcommand = %s, raidcommand = %s, babysitter = %s, timezone = %s, talkgroup = %s, timeformat = %s, icontheme = %s, plusmax = %s, refloatauto = %s;"
        cursor.execute(sql, (group["id"], group["title"], group["alias"], group["spreadsheet"], group["title"], group["alias"], group["spreadsheet"], group["settings_message"], group["alerts"], group["disaggregated"], group["latebutton"], group["refloat"], group["candelete"], group["gotitbuttons"], group["locations"], group["gymcommand"], group["raidcommand"], group["babysitter"], group["timezone"], group["talkgroup"], group["timeformat"], group["icontheme"], group["plusmax"], group["refloatauto"]))
    db.commit()
    db.close()

def getGroup(group_id, reconnect=True):
    db = getDbConnection()
    logging.debug("storagemethods:getGroup: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`title`,`alias`,`spreadsheet`,`testgroup`,`alerts`,`disaggregated`,`settings_message`,`latebutton`,`refloat`,`candelete`,`gotitbuttons`, `locations`, `gymcommand`, `raidcommand`, `babysitter`, `timeformat`, `talkgroup`, `icontheme`, `timezone`, `plusmax`, `refloatauto` FROM `grupos` WHERE `id`=%s"
        try:
            cursor.execute(sql, (group_id))
            result = cursor.fetchone()
        except:
            if reconnect == True:
                logging.info("storagemethods:getGroup Error interfacing with the database! Trying to reconnect...")
                result = getGroup(group_id, False)
            else:
                logging.info("storagemethods:getGroup Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def getGroupsByUser(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getGroupsByUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `grupos`.`id` as `id`, `title`, `alias`, `spreadsheet`, `testgroup`, `alerts`, `disaggregated`, `latebutton`, `refloat`, `candelete`, `gotitbuttons`, `locations`, `gymcommand`, `raidcommand`, `babysitter`, `timeformat`, `talkgroup`, `icontheme`, `timezone` FROM `grupos` \
        LEFT JOIN incursiones ON incursiones.grupo_id = grupos.id \
        RIGHT JOIN voy ON voy.incursion_id = incursiones.id \
        WHERE voy.usuario_id = %s \
        AND voy.addedtime>(DATE_SUB(NOW(),INTERVAL 1 MONTH)) \
		GROUP BY grupos.id"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
    db.close()
    return result

def getValidationsByUser(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getValidationsByUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`, `startedtime`, `step`, `tries`, `pokemon`, `pokemonname`, `usuario_id` FROM `validaciones` \
        WHERE validaciones.usuario_id = %s"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
    db.close()
    return result

def getCurrentValidation(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getCurrentValidation: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`, `startedtime`, `step`, `tries`, `pokemon`, `pokemonname`, `usuario_id`, `trainername`, `team`, `level` FROM `validaciones` \
        WHERE `validaciones`.`usuario_id` = %s AND (`step` = 'waitingtrainername' OR `step` = 'waitingscreenshot' OR `step` = 'failed')"
        cursor.execute(sql, (user_id))
        result = cursor.fetchone()
    db.close()
    return result

def saveValidation(validation):
    db = getDbConnection()
    logging.debug("storagemethods:saveValidation: %s" % (validation))
    for k in ["id","trainername","team","level"]:
        if k not in validation.keys():
            validation[k] = None
    for k in ["tries"]:
        if k not in validation.keys():
            validation[k] = 0
    with db.cursor() as cursor:
        sql = "INSERT INTO validaciones (id, pokemon, pokemonname, usuario_id) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE trainername = %s, step = %s, tries = %s, team = %s, level = %s;"
        cursor.execute(sql, (validation["id"], validation["pokemon"], validation["pokemonname"], validation["usuario_id"], validation["trainername"], validation["step"], validation["tries"], validation["team"], validation["level"]))
    db.commit()
    db.close()
    return True

def getActiveRaidsforUser(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getActiveRaidsforUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT * \
        FROM incursiones \
        WHERE status IN ('started', 'waiting', 'ended') \
            AND addedtime > 0 \
            AND timeraid > 0 \
            AND grupo_id IN ( \
                SELECT `grupos`.`id` AS id \
                FROM `incursiones` \
                LEFT JOIN grupos ON incursiones.grupo_id = grupos.id \
                RIGHT JOIN voy ON voy.incursion_id = incursiones.id \
                WHERE grupos.testgroup = 0 \
                AND voy.usuario_id = %s \
                AND incursiones.addedtime>(DATE_SUB(NOW(),INTERVAL 1 MONTH)) \
                GROUP BY grupos.id \
            ) \
            ORDER BY incursiones.timeraid ASC"
        cursor.execute(sql, (user_id))
        result = cursor.fetchall()
    db.close()
    return result

def getGroupStats(group_id, date_start, date_end):
    db = getDbConnection()
    logging.debug("storagemethods:getGroupStats: %s %s %s" % (group_id, date_start, date_end))
    with db.cursor() as cursor:
        sql = "SELECT voy.usuario_id AS user_id, usuarios.trainername AS trainername, \
        usuarios.username AS username, COUNT(incursiones.id) as incursiones \
        FROM incursiones \
        LEFT JOIN voy ON voy.incursion_id = incursiones.id \
        LEFT JOIN usuarios ON usuarios.id = voy.usuario_id \
        WHERE incursiones.status != 'cancelled' AND incursiones.status != 'deleted' \
        AND timeraid between %s AND %s \
        AND grupo_id = %s \
        AND usuarios.id IS NOT NULL \
        AND usuarios.validation != 'none' \
        GROUP BY voy.usuario_id \
        ORDER BY incursiones DESC"
        cursor.execute(sql, (date_start, date_end, group_id))
        result = cursor.fetchall()
    db.close()
    return result

def getGroupUserStats(group_id, user_id, date_start, date_end):
    db = getDbConnection()
    logging.debug("storagemethods:getGroupUserStats: %s %s %s %s" % (group_id, user_id, date_start, date_end))
    with db.cursor() as cursor:
        sql = "SELECT voy.usuario_id AS user_id, COUNT(incursiones.id) as incursiones \
        FROM incursiones \
        LEFT JOIN voy ON voy.incursion_id = incursiones.id \
        LEFT JOIN usuarios ON usuarios.id = voy.usuario_id \
        WHERE incursiones.status != 'cancelled' AND incursiones.status != 'deleted' \
        AND timeraid between %s AND %s \
        AND grupo_id = %s \
        AND voy.usuario_id = %s \
        AND voy.usuario_id IS NOT NULL \
        AND usuarios.validation != 'none' \
        GROUP BY voy.usuario_id"
        cursor.execute(sql, (date_start, date_end, group_id, user_id))
        result = cursor.fetchone()
    db.close()
    return result

def getActiveRaidsforGroup(group_id):
    db = getDbConnection()
    logging.debug("storagemethods:getActiveRaidsforGroup: %s" % (group_id))
    with db.cursor() as cursor:
        sql = "SELECT * \
        FROM incursiones \
        WHERE status IN ('started', 'waiting', 'ended') \
            AND addedtime > 0 \
            AND timeraid > 0 \
            AND grupo_id = %s \
        ORDER BY incursiones.timeraid ASC"
        cursor.execute(sql, (group_id))
        result = cursor.fetchall()
    db.close()
    return result

def getAutorefloatGroups():
    db = getDbConnection()
    logging.debug("storagemethods:getAutorefloatGroups")
    with db.cursor() as cursor:
        sql = "SELECT id, title FROM grupos WHERE \
            (refloatauto = 5 AND (lastrefloatauto IS NULL OR \
                lastrefloatauto < timestamp(DATE_SUB(NOW(), INTERVAL 5 MINUTE)))) OR \
            (refloatauto = 10 AND (lastrefloatauto IS NULL OR \
                lastrefloatauto < timestamp(DATE_SUB(NOW(), INTERVAL 10 MINUTE)))) OR \
            (refloatauto = 15 AND (lastrefloatauto IS NULL OR \
                lastrefloatauto < timestamp(DATE_SUB(NOW(), INTERVAL 15 MINUTE))))"
        cursor.execute(sql)
        result = cursor.fetchall()
    db.close()
    return result

def updateLastAutorefloat(group_id):
    db = getDbConnection()
    logging.debug("storagemethods:updateLastAutorefloat %s" % group_id)
    with db.cursor() as cursor:
        sql = "UPDATE grupos SET lastrefloatauto = NOW() WHERE id = %s AND refloatauto > 0"
        cursor.execute(sql, group_id)
    db.commit()
    db.close()
    return

def savePlaces(group_id, places):
    db = getDbConnection()
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
            if "tags" not in place.keys():
                place["tags"] = {}
            try:
                sql = "INSERT INTO gimnasios (grupo_id,name,latitude,longitude,keywords,tags) \
                VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE latitude=%s, longitude=%s, keywords=%s, tags=%s;"
                cursor.execute(sql, (group_id, place["desc"], place["latitude"], place["longitude"], json.dumps(place["names"]), json.dumps(place["tags"]), place["latitude"], place["longitude"], json.dumps(place["names"]), json.dumps(place["tags"])))
            except IntegrityError:
                db.rollback()
                db.close()
                return False
    db.commit()
    db.close()
    return True

def getAlerts(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:getAlerts: %s" % (user_id))
    alerts = []
    with db.cursor() as cursor:
        sql = "SELECT `id`,`usuario_id`,`gimnasio_id` FROM `alertas` WHERE `usuario_id`=%s"
        cursor.execute(sql, (user_id))
        for row in cursor:
            alerts.append({"id":row["id"], "user_id":row["usuario_id"], "place_id":row["gimnasio_id"]})
    db.close()
    return alerts

def getAlertsByPlace(place_id):
    db = getDbConnection()
    logging.debug("storagemethods:getAlertsByPlace: %s" % (place_id))
    alerts = []
    with db.cursor() as cursor:
        sql = "SELECT `id`,`usuario_id`,`gimnasio_id` FROM `alertas` WHERE `gimnasio_id`=%s"
        cursor.execute(sql, (place_id))
        for row in cursor:
            alerts.append({"id":row["id"], "user_id":row["usuario_id"], "place_id":row["gimnasio_id"]})
    db.close()
    return alerts

def addAlert(user_id, place_id):
    db = getDbConnection()
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
    db.close()
    return True

def delAlert(user_id, place_id):
    db = getDbConnection()
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
    db.close()
    return True

def clearAlerts(user_id):
    db = getDbConnection()
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
    db.close()
    return True

def getPlaces(group_id, ordering="name"):
    db = getDbConnection()
    logging.debug("storagemethods:getPlaces: %s" % (group_id))
    gyms = []
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`latitude`,`longitude`,`keywords`,`tags` FROM `gimnasios` WHERE `grupo_id`=%s"
        if ordering == "name":
            sql = sql + " ORDER BY name"
        elif ordering == "id":
            sql = sql + " ORDER BY id"
        cursor.execute(sql, (group_id))
        for row in cursor:
            if row["tags"] == None:
                row["tags"] = "[]"
            gyms.append({"id":row["id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"]), "tags":json.loads(row["tags"])})
    db.close()
    return gyms

def getPlace(id):
    db = getDbConnection()
    logging.debug("storagemethods:getPlace: %s" % (id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`name`,`grupo_id`,`latitude`,`longitude`,`keywords`,`tags`,`address` FROM `gimnasios` WHERE `id`=%s"
        cursor.execute(sql, (id))
        for row in cursor:
            if row["tags"] == None:
                row["tags"] = "[]"
            db.close()
            return {"id":row["id"], "group_id":row["grupo_id"], "desc":row["name"], "latitude":row["latitude"], "longitude":row["longitude"], "names":json.loads(row["keywords"]), "tags":json.loads(row["tags"]), "address":row["address"]}
        db.close()
        return None

def savePlace(place):
    db = getDbConnection()
    logging.debug("storagemethods:savePlace: %s" % (place["id"]))
    with db.cursor() as cursor:
        sql = "UPDATE `gimnasios` SET `address`=%s WHERE `id`=%s"
        cursor.execute(sql, (raid["address"], raid["id"]))
    db.commit()
    db.close()

def getPlacesByLocation(latitude, longitude, distance=100):
    db = getDbConnection()
    logging.debug("storagemethods:getPlacesByLocation: %s %s %s" % (latitude, longitude, distance))
    d = float(distance)/50000.0
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`,`latitude`,`longitude`,`name` FROM `gimnasios` WHERE `latitude`> %s AND `latitude` < %s AND `longitude` > %s and `longitude` < %s"
        cursor.execute(sql, (float(latitude)-d,float(latitude)+d,float(longitude)-d,float(longitude)+d))
        result = cursor.fetchall()
    db.close()
    return result

def saveWholeUser(user):
    db = getDbConnection()
    logging.debug("storagemethods:saveWholeUser: %s" % (user))
    with db.cursor() as cursor:
        sql = "INSERT INTO usuarios (id,level,team,username) VALUES (%s, %s, %s, %s) \
        ON DUPLICATE KEY UPDATE level=%s, team=%s, username=%s, banned=%s, trainername=%s, validation=%s;"
        if "validation" not in user.keys():
            user["validation"] = "none"
        if "banned" not in user.keys():
            user["banned"] = 0
        for k in ["trainername","username","team","level"]:
            if k not in user.keys():
                user[k] = None
        cursor.execute(sql, (user["id"], user["level"], user["team"], user["username"], user["level"], user["team"], user["username"], user["banned"], user["trainername"], user["validation"]))
    db.commit()
    db.close()

def saveUser(user):
    db = getDbConnection()
    logging.debug("storagemethods:saveUser: %s" % (user))
    with db.cursor() as cursor:
        sql = "INSERT INTO usuarios (id,username) VALUES (%s, %s) \
        ON DUPLICATE KEY UPDATE username=%s;"
        if "username" not in user.keys():
            user["username"] = None
        cursor.execute(sql, (user["id"], user["username"], user["username"]))
    db.commit()
    db.close()

def refreshUsername(user_id, username):
    db = getDbConnection()
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
    db = getDbConnection()
    logging.debug("storagemethods:getUser: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username`,`banned`,`validation`,`trainername` FROM `usuarios` WHERE `id`=%s"
        try:
            cursor.execute(sql, (user_id))
            result = cursor.fetchone()
        except:
            if reconnect == True:
                logging.info("storagemethods:getUser Error interfacing with the database! Trying to reconnect...")
                result = getUser(user_id, False)
            else:
                logging.info("storagemethods:getUser Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def getUserByTrainername(trainername, reconnect=True):
    db = getDbConnection()
    logging.debug("storagemethods:getUserByTrainername: %s" % (trainername))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`level`,`team`,`username`,`banned`,`validation`,`trainername` FROM `usuarios` WHERE `trainername`=%s"
        try:
            cursor.execute(sql, (trainername))
            result = cursor.fetchone()
        except:
            if reconnect == True:
                logging.info("storagemethods:getUser Error interfacing with the database! Trying to reconnect...")
                getDbConnection()
                result = getUserByTrainername(trainername, False)
            else:
                logging.info("storagemethods:getUser Error interfacing with the database but already tried to reconnect!")
                raise
    db.close()
    return result

def isBanned(user_id):
    db = getDbConnection()
    logging.debug("storagemethods:isBanned: %s" % (user_id))
    with db.cursor() as cursor:
        sql = "SELECT `id` FROM `usuarios` WHERE `id`=%s AND banned=1 UNION SELECT `id` FROM `grupos` WHERE `id`=%s AND banned=1"
        cursor.execute(sql, (user_id, user_id))
        result = cursor.fetchone()
        if result == None:
            db.close()
            return False
        else:
            logging.debug("storagemethods:isBanned: Found banned ID %s" % user_id)
            db.close()
            return True

def saveRaid(raid):
    db = getDbConnection()
    logging.debug("storagemethods:saveRaid: %s" % (raid))
    if "status" not in raid.keys():
        raid["status"] = "waiting"
    if "edited" not in raid.keys():
        raid["edited"] = 0
    if "refloated" not in raid.keys():
        raid["refloated"] = 0
    for k in ["egg","pokemon","timeend","timeraid","message","gimnasio_id"]:
        if k not in raid.keys():
            raid[k] = None
    if "id" not in raid.keys():
        with db.cursor() as cursor:
            sql = "SELECT id FROM grupos WHERE id=%s"
            cursor.execute(sql, (raid["grupo_id"]))
            result = cursor.fetchone()
            if result == None:
                sql = "INSERT INTO grupos (`id`) VALUES (%s);"
                cursor.execute(sql, (raid["grupo_id"]))
            sql = "INSERT INTO incursiones (`grupo_id`, `usuario_id`, `message`, `pokemon`, `egg`,  `gimnasio_id`, `gimnasio_text`, `timeraid`, `timeend`, `status`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            cursor.execute(sql, (raid["grupo_id"], raid["usuario_id"], raid["message"], raid["pokemon"], raid["egg"], raid["gimnasio_id"], raid["gimnasio_text"], raid["timeraid"], raid["timeend"], raid["status"]))
            db.commit()
            db.close()
            return cursor.lastrowid
    else:
        with db.cursor() as cursor:
            sql = "UPDATE incursiones SET `pokemon`=%s, `egg`=%s, `gimnasio_id`=%s, `gimnasio_text`=%s, edited=%s, message=%s, timeraid=%s, timeend=%s, status=%s, refloated=%s WHERE id=%s;"
            cursor.execute(sql, (raid["pokemon"], raid["egg"], raid["gimnasio_id"], raid["gimnasio_text"], raid["edited"], raid["message"], raid["timeraid"], raid["timeend"], raid["status"], raid["refloated"], raid["id"]))
            db.commit()
            db.close()
            return raid["id"]

def getRaid(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:getRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `egg`, `gimnasio_id`, `gimnasio_text`, `edited`, `refloated`, `addedtime`, `timeraid`, `timeend`, `status` FROM `incursiones` WHERE `id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
    db.close()
    return result

def getRaidPeople(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:getRaidPeople: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username`, `trainername`, `plus`, `estoy`, `tarde`, `level`, `team`, `lotengo`, `novoy` FROM `incursiones` \
        LEFT JOIN `voy` ON `voy`.`incursion_id` = `incursiones`.`id` \
        LEFT JOIN `usuarios` ON `usuarios`.`id` = `voy`.`usuario_id` WHERE `incursiones`.`id`=%s \
        ORDER BY `voy`.`addedtime` ASC"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchall()
        if result[0]["id"] == None:
            db.close()
            return None
        else:
            db.close()
            return result

def getRaidbyMessage(grupo_id, message_id):
    db = getDbConnection()
    logging.debug("storagemethods:getRaidByMessage: %s %s" % (grupo_id, message_id))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `egg`, `gimnasio_id`, `gimnasio_text`, `edited`, `refloated`, `addedtime`, `timeraid`, `timeend`, `status` FROM `incursiones` WHERE  grupo_id = %s and `message` = %s"
        cursor.execute(sql, (grupo_id, message_id))
        result = cursor.fetchone()
    db.close()
    return result

def getLastRaids(grupo_id, number):
    db = getDbConnection()
    logging.debug("storagemethods:getlastRaids: %s %s" % (grupo_id, number))
    with db.cursor() as cursor:
        sql = "SELECT `id`,`grupo_id`, `usuario_id`, `message`, `pokemon`, `egg`, `gimnasio_id`, `gimnasio_text`, `edited`, `addedtime`, `timeraid`, `timeend`, `status` FROM `incursiones` WHERE  grupo_id = %s ORDER BY `addedtime` DESC LIMIT 0,%s"
        cursor.execute(sql, (grupo_id, number))
        result = cursor.fetchall()
        if result[0]["id"] == None:
            db.close()
            return None
        else:
            db.close()
            return result

def getCreadorRaid(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:getCreadorRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `usuarios`.`id` AS `id`, `username`,`trainername` FROM `incursiones` LEFT JOIN `usuarios` ON `usuarios`.`id` = `incursiones`.`usuario_id` WHERE `incursiones`.`id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
    db.close()
    return result

def getGrupoRaid(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:getGrupoRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        sql = "SELECT `grupos`.`id` AS `id`, `grupos`.`title` AS `title`, `grupos`.`locations` AS `locations`, `grupos`.`timezone` AS `timezone`, `grupos`.`alias` AS `alias` FROM `incursiones` LEFT JOIN `grupos` ON `grupos`.`id` = `incursiones`.`grupo_id` WHERE `incursiones`.`id`=%s"
        cursor.execute(sql, (raid_id))
        result = cursor.fetchone()
    db.close()
    return result

def raidVoy(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidVoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid["status"] == "ended" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "INSERT INTO voy (incursion_id, usuario_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE plus = 0, estoy = 0, tarde = 0, novoy = 0, lotengo = NULL"
        rows_affected = cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def raidNovoy(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidNovoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid["status"] == "ended" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "SELECT * FROM voy WHERE `incursion_id`=%s and usuario_id=%s and addedtime < timestamp(DATE_SUB(NOW(), INTERVAL 5 MINUTE));"
        cursor.execute(sql, (raid["id"], user_id))
        result = cursor.fetchone()
        if result == None:
            sql = "DELETE FROM voy WHERE `incursion_id`=%s and usuario_id=%s;"
            rows_affected = cursor.execute(sql, (raid["id"], user_id))
        else:
            sql = "UPDATE voy SET novoy=1, estoy = 0, tarde = 0, lotengo = NULL WHERE `incursion_id`=%s and usuario_id=%s;"
            rows_affected = cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def raidPlus1(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidPlus1: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid["status"] == "ended" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        group = getGroup(grupo_id)
        if result != None:
            if result["plus"] >= group["plusmax"]:
                db.close()
                return "demasiados"
            sql = "UPDATE voy SET plus=plus+1, novoy = 0 WHERE `incursion_id`=%s and usuario_id=%s;"
            cursor.execute(sql, (raid["id"], user_id))
        else:
            result = {"plus":0}
            sql = "INSERT IGNORE INTO voy (incursion_id, usuario_id, plus) VALUES (%s, %s, 1)"
            cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    db.close()
    return result["plus"]+1

def raidEstoy(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidEstoy: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid == None or raid["status"] == "ended" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "INSERT INTO voy (incursion_id, usuario_id, estoy) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE estoy=1, tarde=0, novoy=0, lotengo=NULL;"
        rows_affected = cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def raidLlegotarde(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidLlegotarde: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid == None or raid["status"] == "ended" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "INSERT INTO voy (incursion_id, usuario_id, tarde) VALUES (%s, %s, 1) ON DUPLICATE KEY UPDATE tarde=1, estoy=0, novoy=0, lotengo=NULL;"
        rows_affected = cursor.execute(sql, (raid["id"], user_id))
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def raidLotengo(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidLotengo: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid == None or raid["status"] == "waiting" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "SELECT `novoy` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s and novoy = 1"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result != None:
            db.close()
            return "not_going"
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if (result == None and raid["status"] == "started") or result != None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy, lotengo) VALUES (%s, %s, 1, 1) ON DUPLICATE KEY UPDATE tarde=0, estoy=1, novoy=0, lotengo=1;"
            rows_affected = cursor.execute(sql, (raid["id"], user_id))
        else:
            db.close()
            return "not_now"
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def raidEscapou(grupo_id, message_id, user_id):
    db = getDbConnection()
    logging.debug("storagemethods:raidEscapou: %s %s %s" % (grupo_id, message_id, user_id))
    with db.cursor() as cursor:
        raid = getRaidbyMessage(grupo_id, message_id)
        if raid == None:
            db.close()
            return "not_raid"
        if raid == None or raid["status"] == "waiting" or raid["status"] == "old":
            db.close()
            return "old_raid"
        sql = "SELECT `novoy` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s and novoy = 1"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if result != None:
            db.close()
            return "not_going"
        sql = "SELECT `plus` FROM `voy` WHERE `incursion_id`=%s AND `usuario_id`=%s"
        cursor.execute(sql, (raid["id"],user_id))
        result = cursor.fetchone()
        if (result == None and raid["status"] == "started") or result != None:
            sql = "INSERT INTO voy (incursion_id, usuario_id, estoy, lotengo) VALUES (%s, %s, 1, 1) ON DUPLICATE KEY UPDATE tarde=0, estoy=1, novoy=0, lotengo=0;"
            rows_affected = cursor.execute(sql, (raid["id"], user_id))
        else:
            return "not_now"
    db.commit()
    db.close()
    if rows_affected > 0:
        return True
    else:
        return "no_changes"

def deleteRaid(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:deleteRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        raid = getRaid(raid_id)
        if raid["status"] == "deleted":
            db.close()
            return "already_deleted"
        elif raid["status"] == "old" or raid["status"] == "ended":
            db.close()
            return "too_old"
        else:
            sql = "UPDATE incursiones SET `status`='deleted' WHERE id=%s;"
            cursor.execute(sql, (raid_id))
            db.commit()
    db.close()
    return True

def cancelRaid(raid_id):
    db = getDbConnection()
    logging.debug("storagemethods:cancelRaid: %s" % (raid_id))
    with db.cursor() as cursor:
        raid = getRaid(raid_id)
        if raid["status"] == "cancelled":
            return "already_cancelled"
        elif raid["status"] == "old" or raid["status"] == "ended":
            return "too_old"
        elif raid["status"] == "deleted":
            return "already_deleted"
        else:
            sql = "UPDATE incursiones SET `status`='cancelled' WHERE id=%s;"
            cursor.execute(sql, (raid_id))
            db.commit()
    db.close()
    return True

def updateRaidsStatus():
    db = getDbConnection()
    logging.debug("storagemethods:updateRaidsStatus")
    raidstoupdate = []
    try:
        # Set raids as old
        with db.cursor() as cursor:
            sql = "SELECT `incursiones`.`id` AS `id`, `timeraid`, `timezone` FROM `incursiones` LEFT JOIN grupos ON `incursiones`.`grupo_id` = `grupos`.`id` WHERE status = 'ended' and timeraid > 0 LIMIT 0,2000"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                try:
                    threehoursago_datetime = datetime.now(timezone(r["timezone"])).replace(tzinfo=timezone(r["timezone"])) - timedelta(minutes = 180)
                    raid_datetime = r["timeraid"].replace(tzinfo=timezone(r["timezone"]))
                    if raid_datetime < threehoursago_datetime:
                        logging.debug("storagemethods:updateRaidsStatus marking raid %s as old because %s < %s" % (r["id"],raid_datetime,threehoursago_datetime))
                        sql = "UPDATE incursiones SET `status`='old' WHERE id=%s;"
                        cursor.execute(sql, (r["id"]))
                        raidstoupdate.append(r)
                except Exception as e:
                    logging.debug("supportmethods:updateRaidsStatus error: %s" % str(e))
        # Set raids as ended
        with db.cursor() as cursor:
            sql = "SELECT `incursiones`.`id` AS `id`, `timeraid`, `timezone` FROM `incursiones` LEFT JOIN grupos ON `incursiones`.`grupo_id` = `grupos`.`id` WHERE status = 'started' and timeraid > 0 LIMIT 0,2000"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                try:
                    thirtyminsago_datetime = datetime.now(timezone(r["timezone"])).replace(tzinfo=timezone(r["timezone"])) - timedelta(minutes = 30)
                    raid_datetime = r["timeraid"].replace(tzinfo=timezone(r["timezone"]))
                    if raid_datetime < thirtyminsago_datetime:
                        logging.debug("storagemethods:updateRaidsStatus marking raid %s as ended because %s < %s" % (r["id"],raid_datetime,thirtyminsago_datetime))
                        sql = "UPDATE incursiones SET `status`='ended' WHERE id=%s;"
                        cursor.execute(sql, (r["id"]))
                        raidstoupdate.append(r)
                except Exception as e:
                    logging.debug("supportmethods:updateRaidsStatus error: %s" % str(e))
        # Set raids as started
        with db.cursor() as cursor:
            sql = "SELECT `incursiones`.`id` AS `id`, `timeraid`, `timezone` FROM `incursiones` LEFT JOIN grupos ON `incursiones`.`grupo_id` = `grupos`.`id` WHERE status = 'waiting' and timeraid > 0 LIMIT 0,2000"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                logging.debug(r)
                try:
                    now_datetime = datetime.now(timezone(r["timezone"])).replace(tzinfo=timezone(r["timezone"]))
                    raid_datetime = r["timeraid"].replace(tzinfo=timezone(r["timezone"]))
                    if raid_datetime < now_datetime:
                        logging.debug("storagemethods:updateRaidsStatus marking raid %s as started because %s < %s" % (r["id"],raid_datetime,now_datetime))
                        sql = "UPDATE incursiones SET `status`='started' WHERE id=%s;"
                        cursor.execute(sql, (r["id"]))
                        raidstoupdate.append(r)
                except Exception as e:
                    logging.debug("supportmethods:updateRaidsStatus error: %s" % str(e))
    except Exception as e:
        logging.debug("supportmethods:updateRaidsStatus error: %s" % str(e))
    db.commit()
    db.close()
    return raidstoupdate

def updateValidationsStatus():
    db = getDbConnection()
    logging.debug("storagemethods:updateValidationsStatus")
    validationstoupdate = []
    try:
        with db.cursor() as cursor:
            sql = "SELECT * FROM `validaciones` WHERE (step = 'waitingtrainername' OR step = 'waitingscreenshot' OR step = 'failed') and startedtime < timestamp(DATE_SUB(NOW(), INTERVAL 6 HOUR)) LIMIT 0,2000"
            cursor.execute(sql)
            results = cursor.fetchall()
            for r in results:
                logging.debug(r)
                try:
                    logging.debug("storagemethods:updateValidationsStatus marking validation %s as expired" % (r["id"]))
                    sql = "UPDATE validaciones SET `step`='expired' WHERE id=%s;"
                    cursor.execute(sql, (r["id"]))
                    validationstoupdate.append(r)
                except Exception as e:
                    logging.debug("supportmethods:updateValidationsStatus error: %s" % str(e))
    except Exception as e:
        logging.debug("supportmethods:updateValidationsStatus error: %s" % str(e))
    db.commit()
    db.close()
    return validationstoupdate
