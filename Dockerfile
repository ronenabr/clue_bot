FROM python:3

RUN git clone https://github.com/ronenabr/clue_bot.git && \
    cd clue_bot && \
    pip install -r requiremnts.txt

RUN echo foo && \
    cd clue_bot && \
    git fetch && \
    git pull && \
    chmod a+x bot.py


COPY bot_token.py clue_bot/bot_token.py