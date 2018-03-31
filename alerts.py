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

import telegram
import logging
import gettext

from supportmethods import delete_message, edit_check_private, extract_update_info, ensure_escaped
from storagemethods import getAlerts, getPlace, getGroup, isBanned, delAlert, addAlert, clearAlerts, getPlacesByLocation, getGroupsByUser


def alerts(bot, update, args=None):
    logging.debug("detectivepikachubot:alerts: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if user_id is not None and isBanned(user_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "alerts", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    alerts = getAlerts(user_id)

    if not len(alerts):
        text_message = _("🔔 No tienes ninguna alerta de incursión definida.")

    else:
        text_message = _("🔔 Tienes definidas {0} alertas para los siguientes gimnasios:\n").format(len(alerts))

        for alert in alerts:
            place = getPlace(alert["place_id"])
            group = getGroup(place["group_id"])
            text_message = text_message + _("\n✅ `{0}` {1} - Grupo {2}").format(place["id"], ensure_escaped(place["desc"]), ensure_escaped(group["title"]))

        text_message = text_message + _("\n\nPara borrar una alerta, envíame `/delalert` seguido del identificador numérico, o `/clearalerts` para borrarlas todas.")
    text_message = text_message + _("\n\nPara añadir alertas de incursión nuevas, *envíame una ubicación* con gimnasios cercanos (_usando la función de Telegram de enviar ubicaciones_) y te explico.")
    bot.send_message(chat_id=user_id, text=text_message, parse_mode=telegram.ParseMode.MARKDOWN)


def addalert(bot, update, args=None):
    logging.debug("detectivepikachubot:addalert: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if user_id is not None and isBanned(user_id):
        return

    if edit_check_private(chat_id, chat_type, user_username, "addalert", bot) == False:
        delete_message(chat_id, message.message_id, bot)
        return

    if len(args) < 1 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text=_("❌ ¡Tienes que pasarme un identificador numérico como parámetro!"), parse_mode=telegram.ParseMode.MARKDOWN)
        return

    alerts = getAlerts(user_id)

    if len(alerts) >= 25:
        bot.sendMessage(chat_id=chat_id, text=_("❌ ¡Solo se pueden configurar un máximo de {0} alertas!").format(25), parse_mode=telegram.ParseMode.MARKDOWN)
        return

    place = getPlace(args[0])
    if place is None:
        bot.sendMessage(chat_id=chat_id, text=_("❌ ¡No he reconocido ese gimnasio! ¿Seguro que has puesto bien el identificador?"), parse_mode=telegram.ParseMode.MARKDOWN)
        return

    for alert in alerts:
        if alert["place_id"] == place["id"]:
            bot.sendMessage(chat_id=chat_id, text=_("❌ ¡Ya has configurado una alerta para ese gimnasio!"), parse_mode=telegram.ParseMode.MARKDOWN)
            return

    if addAlert(user_id, place["id"]):
        bot.sendMessage(chat_id=chat_id, text=_("👌 Se ha añadido una alerta para el gimnasio *{0}*.\n\nA partir de ahora, recibirás un mensaje privado cada vez que alguien cree una incursión en ese gimnasio.").format(ensure_escaped(place["desc"])), parse_mode=telegram.ParseMode.MARKDOWN)

    else:
        bot.sendMessage(chat_id=chat_id, text=_("❌ No se ha podido añadir una alerta para ese gimnasio."), parse_mode=telegram.ParseMode.MARKDOWN)


def delalert(bot, update, args=None):
    logging.debug("detectivepikachubot:delalert: %s %s %s" % (bot, update, args))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if user_id is not None and isBanned(user_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "delalert", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    if len(args)<1 or not str(args[0]).isnumeric():
        bot.sendMessage(chat_id=chat_id, text=_("❌ ¡Tienes que pasarme un identificador numérico como parámetro!"), parse_mode=telegram.ParseMode.MARKDOWN)
        return

    place = getPlace(args[0])
    if place is None:
        bot.sendMessage(chat_id=chat_id, text=_("❌ ¡No he reconocido ese gimnasio! ¿Seguro que has puesto bien el identificador?"), parse_mode=telegram.ParseMode.MARKDOWN)
        return

    if delAlert(user_id, place["id"]):
        bot.sendMessage(chat_id=chat_id, text=_("👌 Se ha eliminado la alerta del gimnasio *{0}*.\n\nA partir de ahora, ya no recibirás mensajes privados cada vez que alguien cree una incursión allí.").format(ensure_escaped(place["desc"])), parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text=_("❌ No se ha podido eliminar la alerta para ese gimnasio."), parse_mode=telegram.ParseMode.MARKDOWN)

def clearalerts(bot, update):
    logging.debug("detectivepikachubot:clearlerts: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    user_username = message.from_user.username

    if isBanned(chat_id):
        return

    if user_id is not None and isBanned(user_id):
        return

    if not edit_check_private(chat_id, chat_type, user_username, "clearalerts", bot):
        delete_message(chat_id, message.message_id, bot)
        return

    if clearAlerts(user_id):
        bot.sendMessage(chat_id=chat_id, text=_("👌 Se han eliminado las alertas de todos los gimnasios.\n\nA partir de ahora, ya no recibirás mensajes privados cada vez que alguien cree una incursión."), parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.sendMessage(chat_id=chat_id, text=_("❌ No se ha eliminado ninguna alerta."), parse_mode=telegram.ParseMode.MARKDOWN)

def processLocation(bot, update):
    logging.debug("detectivepikachubot:processLocation: %s %s" % (bot, update))
    (chat_id, chat_type, user_id, text, message) = extract_update_info(update)
    location = message.location

    if isBanned(chat_id):
        return

    if user_id is not None and isBanned(user_id):
        return

    if chat_type == "private":
        places = getPlacesByLocation(location.latitude, location.longitude, 200)
        logging.debug(places)
        filtered_places = []
        for place in places:
            group = getGroup(place["grupo_id"])
            if group["testgroup"] == 1 or group["alerts"] == 0:
                continue
            ingroup = False
            groups = getGroupsByUser(user_id)
            for g in groups:
                if group["id"] == g["id"]:
                    ingroup = True
            if ingroup == False:
                continue
            filtered_places.append(place)
        if len(filtered_places) == 0:
            bot.sendMessage(chat_id=chat_id, text=_("❌ No se han encontrado gimnasios cerca de esta zona en grupos en los que hayas participado en una incursión recientemente. Ten en cuenta que el radio de búsqueda es de aproximadamente 180 metros."), parse_mode=telegram.ParseMode.MARKDOWN)
        else:
            text_message = _("🗺 Se han encontrado los siguientes gimnasios:\n")
            example_id = None
            alerts = getAlerts(user_id)
            alert_ids = []
            for alert in alerts:
                alert_ids.append(alert["place_id"])
            for place in filtered_places:
                group = getGroup(place["grupo_id"])
                if example_id is None:
                    example_id = place["id"]
                if place["id"] in alert_ids:
                    icon = "✅"
                else:
                    icon = "▪️"
                text_message = text_message + "\n%s `%s` %s - Grupo %s" % (icon, place["id"], ensure_escaped(place["name"]), ensure_escaped(group["title"]))
            text_message = text_message + _("\n\nPara añadir una alerta para alguno de estos gimnasios, envíame el comando `/addalert` seguido del identificador numérico.\n\nPor ejemplo:\n`/addalert {0}`").format(example_id)
            bot.sendMessage(chat_id=chat_id, text=text_message, parse_mode=telegram.ParseMode.MARKDOWN)
