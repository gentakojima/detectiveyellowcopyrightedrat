# Detective YellowCopyrightedRat

A Telegram Bot to create raids and show gym locations for Pokémon GO. Last version is always up and running in [@detectivepikachubot](https://t.me/detectivepikachubot). The bot is currently in Spanish only.

## Requirements

Requires Python 3.4+ and a MySQL 5.5+ or MariaDB database.

To install the required Python libraries, just run:

```bash
sudo pip3 install -r requirements.txt
```

The system package `tesseract-ocr` is also required. To install it in Debian-based systems, just run:

```bash
sudo apt-get install tesseract-ocr
```

## Configuration

After the first run, an example configuration file will be written in `~/.config/detectivepikachu/config.ini` containing three sections:

* `database` to configure the connection to the MySQL database
* `telegram` to configure the Telegram bot Token
* `googlemaps` to configure the Google Maps API key

The database should be initialized manually with the contents of `schema.sql`. The user must have access to the application schema and read-only access to the built-in `mysql` schema.

You must load the timezone info into the `mysql` schema. This is usually done by the script `mysql_tzinfo_to_sql` included in MySQL distributions. Look at [the MySQL manual](https://dev.mysql.com/doc/refman/5.5/en/mysql-tzinfo-to-sql.html) for more details.

After all that hard work, you should be up and running!

## Contributing

Notify errors and ask for new features in the issue tracker. You can also propose changes by sending pull requests directly to master.

To contribute to translations go to [the Telegram help group](https://t.me/detectivepikachuayuda) to say hi and [request access to the Poeditor platform](https://poeditor.com/join/project/ptifyZlsJv). Translations are not automatically synced from Poeditor, and translating them by pull request in Github could end up in duplicated efforts.

## License

Copyright (C) 2017 Jorge Suárez de Lis <hey@gentakojima.me>

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.
