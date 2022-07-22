# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

FROM python:3.7-slim
USER root

# leaderboard
ENV TZ 'Asia/Taipei'

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN apt-get update && apt-get install -y libpq-dev gcc

WORKDIR /app
COPY . /app

ENTRYPOINT ["python3"]
CMD ["main.py"]