#!/bin/bash
set -u
cd "$(dirname "$0")"
jar_path=${FREEROUTING_JAR:?Set FREEROUTING_JAR to the verified Freerouting 2.3.0 jar}
java_path=${FREEROUTING_JAVA:-java}
sha256sum input.dsn "$jar_path" > tool-input-sha256.txt
"$java_path" -version > java-version.txt 2>&1
timeout 240 "$java_path" -Djava.awt.headless=true -jar "$jar_path" -de input.dsn -do strict.ses -mp 30 -mt 1 --router.fanout.enabled=false --router.automatic_neckdown=false --router.optimizer.enabled=true --router.optimizer.max_threads=1 --user_data_path="$PWD/user-data" > route.log.txt 2>&1
r=$?
echo "$r" > route.exit
exit "$r"
