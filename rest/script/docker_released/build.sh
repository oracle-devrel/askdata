# cp is needed for user mode
# cp -r ~/.oci ./oci
# The release name is the top most directory within the zip file 
# This is the structure given by the orahub.
# Dependency
# 1. Need the release file in the current directory. Do it outside of the git structure
# 2. Copy (and fix) the oci config file and key file (if used in oci user mode)
docker build --progress=plain --build-arg RELEASE_FILE=nl2sql-2025W19.zip --build-arg RELEASE_NAME=nl2sql-2025W19 -t nl2sql-trust:2025w19 .
