<?php
namespace App\Classes;

use Logger;
use Illuminate\Support\Facades\DB;

class BulkInsert {

    private $bulk_size;
    private $records;
    private $table_name;
    private $database_connection;

    /**
     * @return $bulk_size
     */
    public function getBulkSize() {
        return $this->bulk_size;
    }

    /**
     * @param $bulk_size valorize instance attribute @ref $bulk_size
     */
    public function setBulkSize($bulk_size) {
        $this->bulk_size = $bulk_size;
    }

    /**
     * @return $records
     */
    public function getRecords() {
        return $this->records;
    }

    /**
     * @param $records valorize instance attribute @ref $records
     */
    public function setRecords($records) {
        $this->records = $records;
    }

    /**
     * @return $table_name
     */
    public function getTableName() {
        return $this->table_name;
    }

    /**
     * @param $table_name valorize instance attribute @ref $table_name
     */
    public function setTableName($table_name) {
        $this->table_name = $table_name;
    }

    /**
     * @return $databse_connection
     */
    public function getDatabaseConnection() {
        return $this->database_connection;
    }

    /**
     * @param $databse_connection valorize instance attribute @ref $databse_connection
     */
    public function setDatabaseConnection($database_connection) {
        $this->database_connection = $database_connection;
    }


    public function __construct($table_name, $records=[], $bulk_size=2000, $database_connection=NULL) {
        $this->table_name = $table_name;
        $this->records = $records;
        $this->bulk_size = $bulk_size;
        if (!is_null($database_connection)) {
            $this->database_connection = $database_connection;
        }
    }

    public function save($records=[], $bulk_size=null) {
        $total = 0;
        $bulk_cnt = 0;
        if (!is_null($records) && !empty($records)) {
            $this->records = $records;
        }
        if ($bulk_size && $bulk_size > 0) {
            $this->bulk_size = $bulk_size;
        }
        $cnt = 0;
        $bulk = [];
        foreach ($this->records as $record) {
            $total++;
            $cnt++;
            $bulk[] = $record;
            if ($cnt >= $this->bulk_size) {
                DB::connection($this->database_connection)
                    ->table($this->table_name)
                    ->insert($bulk);
                $cnt = 0;
                $bulk = [];
                $bulk_cnt++;
            }
        }
        if (count($bulk) > 0)  {
            DB::connection($this->database_connection)
                ->table($this->table_name)
                ->insert($bulk);
            $bulk_cnt++;
        }
        $msg = sprintf(
            "Stored %d records in `%s` by %d bulks of %d records",
            $total,
            $this->table_name,
            $bulk_cnt,
            $this->bulk_size
        );
        Logger::info($msg);
    }
}
