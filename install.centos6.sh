#!/bin/bash
# To be run as root or with root permissions

PG_VERSION=postgresql92

# Install PostgreSQL
yum install -y $PG_VERSION-postgresql-server $PG_VERSION-postgresql-devel $PG_VERSION-postgresql

# Build RDKit Extension (Requires RDKit to already be built in $RDBASE)
pushd $RDBASE/Code/PgSQL/rdkit
cp -v Makefile Makefile~
sed -i 's/USE_INCHI=0/USE_INCHI=1/g' Makefile  # Build with InChI support
# Ensure we use the Postgresql9.2 binaries, libraries, and config using scl enable
scl enable $PG_VERSION "make"
scl enable $PG_VERSION "make install"
popd

# Add rdkit to libraries to load for all clients
PG_ROOT=$( cat /etc/scl/prefixes/$PG_VERSION )/$PG_VERSION/root
PG_CONFIG=$PG_ROOT/var/lib/pgsql/data/postgresql.conf
echo "shared_preload_libraries = 'rdkit'" >> $PG_CONFG

# Setup PostgreSQL
service $PG_VERSION-postgresql initdb
service $PG_VERSION-postgresql start

# Enter user password
DB='agad'
USER='agad'
PW='agad'
scl enable $PG_VERSION "printf '$PW\n$PW\n' | createuser --echo --pwprompt $USER"
scl enable $PG_VERSION "createdb --echo --owner $USER $DB"

python aggregatoradvisor/init.db
