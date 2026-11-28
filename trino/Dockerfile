# Trino for Task 5: the official image + the SQLite JDBC driver.
# The driver lets Trino's Iceberg connector read the SAME SQLite catalog file that
# PyIceberg created in Task 3 (Trino only ships the PostgreSQL driver for JDBC catalogs).
FROM trinodb/trino:476

ADD --chmod=644 https://repo1.maven.org/maven2/org/xerial/sqlite-jdbc/3.46.1.0/sqlite-jdbc-3.46.1.0.jar \
    /usr/lib/trino/plugin/iceberg/sqlite-jdbc-3.46.1.0.jar
