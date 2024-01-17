#!/bin/bash

# https://stackoverflow.com/a/246128
DIR="$( dirname $(readlink -f "$0") )"

LOG_FILE=$DIR/StadtBibliothek.log
[ ! -f $LOG_FILE ] && touch $LOG_FILE

JUST_THE_LATEST_PART_OF_THE_LOG_FILE=$( tail -1000 $LOG_FILE )
echo "$JUST_THE_LATEST_PART_OF_THE_LOG_FILE" > $LOG_FILE
date >> $LOG_FILE
echo DIR=$DIR >> $LOG_FILE

$DIR/venv/bin/python3 $DIR/StadtBibliothek.py 2>&1 | tee -a $LOG_FILE
