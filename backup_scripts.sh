#!/bin/bash

BACKUPDIR=/home/pi/data/syncaod/TCA/scripts
SCRIPTDIR=/home/pi/TCA

# Check if backup directory exists
if [ ! -d "$BACKUPDIR" ];
   then
      echo "Backup directory $BACKUPDIR doesn't exist, creating it now!"
      mkdir $DIR
fi

# Create a filename with datestamp for our current backup (without .zip suffix)
OFILE="$BACKUPDIR/pythonscripts_$(date +%Y%m%d_%H%M%S)"

# Create final filename, with suffix
OFILEFINAL=$OFILE.zip

cd $SCRIPTDIR
zip $OFILEFINAL ./*
