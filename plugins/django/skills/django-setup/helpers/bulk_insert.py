from django.db import DEFAULT_DB_ALIAS, connections

from core.__PREFIX___utils.logger import Logger


class BulkInsert:
    """
    Inserts a list of records (dicts with the same keys) in a table, in
    chunks of bulk_size records. Works on SQLite, PostgreSQL and
    MySQL/MariaDB.
    """

    def __init__(
        self, table_name, records=None, bulk_size=2000, using=None
    ):
        self.table_name = table_name
        self.records = records if records is not None else []
        self.bulk_size = bulk_size
        self.using = using or DEFAULT_DB_ALIAS

    def save(self, records=None, bulk_size=None):
        if records:
            self.records = records
        if bulk_size and bulk_size > 0:
            self.bulk_size = bulk_size

        total = 0
        bulk_cnt = 0
        bulk = []
        for record in self.records:
            total += 1
            bulk.append(record)
            if len(bulk) >= self.bulk_size:
                self._insert(bulk)
                bulk = []
                bulk_cnt += 1
        if bulk:
            self._insert(bulk)
            bulk_cnt += 1

        msg = "Stored {} records in `{}` by {} bulks of {} records"
        Logger.info(
            msg.format(total, self.table_name, bulk_cnt, self.bulk_size)
        )

    def _insert(self, bulk):
        connection = connections[self.using]
        quote = connection.ops.quote_name
        columns = list(bulk[0].keys())
        row = "({})".format(", ".join(["%s"] * len(columns)))

        # Some backends (SQLite) limit the parameters of a query: split
        # the chunk in as many INSERTs as needed
        size = len(bulk)
        max_params = connection.features.max_query_params
        if max_params:
            size = max(1, min(size, max_params // len(columns)))

        query = "INSERT INTO {} ({}) VALUES {}"
        with connection.cursor() as cursor:
            for start in range(0, len(bulk), size):
                rows = bulk[start:start + size]
                sql = query.format(
                    quote(self.table_name),
                    ", ".join(quote(column) for column in columns),
                    ", ".join([row] * len(rows)),
                )
                params = [
                    record[column] for record in rows for column in columns
                ]
                cursor.execute(sql, params)
