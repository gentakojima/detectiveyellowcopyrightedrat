# Detective YellowCopyrightedRat

A Telegram Bot to create raids and show gym locations for Pokémon GO. Last version is always up and running in [@detectivepikachubot](https://t.me/detectivepikachubot). The bot is currently in Spanish only.

## Requeriments

Requires Python 3,4+ and a MySQL 5.5+ or MariaDB database.

To install the required Python libraries, just run:

```
pip3 install -r requeriments.txt
```

## Configuration

After the first run, an example configuration file will be written in `~/.config/detectivepikachu/config.ini` containing three sections:
 * `database` to configure the connection to the MySQL database
 * `telegram` to configure the Telegram bot Token
 * `googlemaps` to configure the Google Maps API key

The database should be initialized manually with the contents of `schema.sql`.

After all that hard work, you should be up and running!

## License

Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see http://www.gnu.org/licenses/.
