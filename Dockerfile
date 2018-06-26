FROM python:3

RUN git clone https://github.com/ronenabr/clue_bot.git && \
    cd clue_bot && \
    pip install -r requiremnts.txt

RUN cd clue_bot && \
    git fetch && \
    git pull

COPY bot_token.py clue_bot/bot_token.py