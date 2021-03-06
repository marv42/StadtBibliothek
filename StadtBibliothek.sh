#!/bin/bash

# https://stackoverflow.com/a/246128

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

LOG_FILE=$DIR/StadtBibliothek.log
[ ! -f $LOG_FILE ] && touch $LOG_FILE

JUST_THE_LATEST_PART_OF_THE_LOG_FILE=$( tail -1000 $LOG_FILE )
echo "$JUST_THE_LATEST_PART_OF_THE_LOG_FILE" > $LOG_FILE
date >> $LOG_FILE
echo DIR=$DIR >> $LOG_FILE
echo SOURCE=$SOURCE >> $LOG_FILE

$DIR/venv/bin/python3 $DIR/StadtBibliothek.py 2>&1 | tee -a $LOG_FILE
