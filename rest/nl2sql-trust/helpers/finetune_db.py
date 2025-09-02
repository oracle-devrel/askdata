# Copyright (c) 2021, 2025 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import datetime
import logging
import constants
import oracledb

from typing import Dict, Any, List, Optional, Tuple
import helpers.database_util as iou
from helpers.config_json_helper import config_boostrap as confb
from datetime import datetime
import pandas as pd


logger = logging.getLogger(constants.FINETUNE_LAYER)

class FineTuneWorkflowDAO:
    """Data Access Object for FINETUNE_WORKFLOW table operations"""
    
    
    def create(self, req: Dict[str, Any]) -> str:
        # Ensure workflow_key is provided or generate one
        workflow_key = req.get('workflow_key')
        if not workflow_key:
            raise ValueError("workflow_key is required")
            
        insert_sql = """
            INSERT INTO FINETUNE_WORKFLOW (
                WORKFLOW_KEY, TRAINING_DATA_ID, MODEL_DESCR, UNIT_COUNT, UNIT_SHAPE,
                CONFIG_STATE, CONFIG_SUBMIT_TIME, DAC_CREATED_TIME, DAC_LIFECYCLE_STATE,
                DAC_SUBMIT_TIME, DAC_CLUSTER_ID, DAC_ERROR_DTLS, DAC_UNIT_COUNT, DAC_UNIT_SHAPE,
                DAC_STARTED_TIME, FT_SUBMIT_TIME, FT_CREATED_TIME, FT_BASE_MODEL_ID, FT_LIFECYCLE_STATE,
                FT_RESULT_MODEL_ID, FT_TYPE, FT_VERSION, FT_COMPLETION_TIME, FT_ERROR_DTLS,
                EVAL_START_TIME, EVAL_END_TIME
            ) VALUES (
                :workflow_key, :training_data_id, :model_descr, :unit_count, :unit_shape,
                :config_state, :config_submit_time, :dac_created_time, :dac_lifecycle_state,
                :dac_submit_time, :dac_cluster_id, :dac_error_dtls, :dac_unit_count, :dac_unit_shape,
                :dac_started_time, :ft_submit_time, :ft_created_time, :ft_base_model_id, :ft_lifecycle_state,
                :ft_result_model_id, :ft_type, :ft_version, :ft_completion_time, :ft_error_dtls,
                :ft_eval_start_time, :ft_eval_end_time
            )
        """
                
        params = {
            'workflow_key': workflow_key,
            'training_data_id': req.get('training_data_id'),
            'model_descr': req.get('model_descr'),
            'unit_count': req.get('unit_count'),
            'unit_shape': req.get('unit_shape'),
            'config_state': req.get('config_state'),
            'config_submit_time': req.get('config_submit_time'),
            'dac_submit_time': req.get('dac_submit_time'),
            'dac_created_time': req.get('dac_created_time'),
            'dac_lifecycle_state': req.get('dac_lifecycle_state'),
            'dac_cluster_id': req.get('dac_cluster_id'),
            'dac_error_dtls': req.get('dac_error_dtls'),
            'dac_unit_count': req.get('dac_unit_count'),
            'dac_unit_shape': req.get('dac_unit_shape'),
            'dac_started_time': req.get('dac_started_time'),
            'ft_submit_time': req.get('ft_submit_time'),
            'ft_created_time': req.get('ft_created_time'),
            'ft_base_model_id': req.get('ft_base_model_id'),
            'ft_lifecycle_state': req.get('ft_lifecycle_state'),
            'ft_result_model_id': req.get('ft_result_model_id'),
            'ft_type': req.get('ft_type'),
            'ft_version': req.get('ft_version'),
            'ft_completion_time': req.get('ft_completion_time'),
            'ft_error_dtls': req.get('ft_error_dtls'),
            'ft_eval_start_time': req.get('ft_eval_start_time'),
            'ft_eval_end_time': req.get('ft_eval_end_time')
        }
        
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(insert_sql, params)
                connection.commit()
                return workflow_key
        except oracledb.Error as e:
            raise Exception(f"Failed to create workflow: {str(e)}")
    
    def update(self,workflow_key:str, req: Dict[str, Any]) -> bool:
        logger.info(f"workflow {workflow_key} update entry {req}")
        if not workflow_key:
            raise ValueError("workflow_key is required for update")
        
        # Build dynamic update SQL based on provided fields
        update_clauses = []
        params = {'workflow_key': workflow_key}
        
        # Map of possible fields to update
        possible_fields = [
            'training_data_path', 'training_data_id', 'model_descr', 'unit_count', 'unit_shape', 'deploy_state', 'model_usage_id',
            'config_state', 'config_submit_time', 'dac_submit_time', 'dac_lifecycle_state', 'dac_created_time', 'dac_destroy_time',
            'dac_cluster_id', 'dac_error_dtls', 'dac_unit_count', 'dac_unit_shape',
            'dac_started_time', 'ft_submit_time', 'ft_created_time', 'ft_base_model_id', 'ft_lifecycle_state',
            'ft_result_model_id', 'ft_type', 'ft_version', 'ft_completion_time', 'ft_error_dtls','eval_start_time','eval_end_time'
        ]
        
        # Add each provided field to the update statement
        for field in possible_fields:
            if field in req:
                update_clauses.append(f"{field.upper()} = :{field}")
                params[field] = req[field]
        
        # If no fields to update
        if not update_clauses:
            logger.info("FineTuneWorkflowDAO: No update clause, returning false.")
            return False
        
        update_sql = f"""
            UPDATE FINETUNE_WORKFLOW
                SET {', '.join(update_clauses)}
                WHERE WORKFLOW_KEY = :workflow_key
            """
        logger.info(f"finetune workflow update sql = {update_sql}")
        logger.info(f"finetune workflow update params = {params}")
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(update_sql, params)
                    rows_updated = cursor.rowcount
                connection.commit()

                logger.info(f"finetune workflow rows updated = {rows_updated}")
                return rows_updated > 0
        except oracledb.Error as e:
            raise Exception(f"Failed to update workflow: {str(e)}")
    
    def delete(self, workflow_key: str) -> bool:
        if not workflow_key:
            raise ValueError("workflow_key is required for delete")
        
        delete_sql = "DELETE FROM FINETUNE_WORKFLOW WHERE WORKFLOW_KEY = :workflow_key"
        
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(delete_sql, {'workflow_key': workflow_key})
                    rows_deleted = cursor.rowcount
                connection.commit()
                return rows_deleted > 0
        except oracledb.Error as e:
            raise Exception(f"Failed to delete workflow: {str(e)}")
    
    def get_by_key(self, workflow_key: str) -> Optional[Dict[str, Any]]:
        select_sql = "SELECT * FROM FINETUNE_WORKFLOW WHERE WORKFLOW_KEY = :workflow_key"
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(select_sql, {'workflow_key': workflow_key})
                    columns = [col[0].lower() for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        return dict(zip(columns, row))
                    return None
        except oracledb.Error as e:
            raise Exception(f"Failed to retrieve workflow: {str(e)}")

    def get_finetune_history(self,domain):
        # Execute sql
        sql = f"""  select 
                        to_char(config_submit_time, '{confb.dconfig["database"]["date_format"]}') as fine_tune_date, 
                        workflow_key as model_name, 
                        (case when model_descr is null then ' ' else model_descr end) model_description,
                        t.filename as training_data_filename,
                        t.record_count as record_count,
                        (case when ft_version is null then ' ' else ft_version end) model_version,
                        (case when deploy_state is null then ' ' else deploy_state end) deploy_status,
                        (case when m.usage_start is null then ' ' else to_char(m.usage_start, '{confb.dconfig["database"]["date_format"]}') end) deployment_date
                    from finetune_workflow w
                    left outer join model_usage m on m.workflow_id = w.id
                    left outer join trainingdata_history t on t.id = w.training_data_id
                    where w.config_state = 'set'
                    order by w.id """

        connection = iou.db_get_connection()
        sql_ret = iou.db_select(connection=connection, select_statement=sql)
        connection.close()
        # -- NEW -------------------------------------------------------------
        # augment sql records with evaluation fields for each workflow key
        sql_ret_augmented = []
        for ret in sql_ret:
            sql_record_augmented = ret
            eval_dict = self.get_evaluate_finetune(ret[1])
            regression_result = f'{eval_dict["regression_accuracy"]} (n={eval_dict["regression_count"]})'
            corrected_result = f'{eval_dict["corrected_accuracy"]} (n={eval_dict["corrected_count"]})'
            sql_record_augmented = ret + (regression_result, corrected_result, )
            sql_ret_augmented.append(sql_record_augmented)
        # -- end NEW -------------------------------------------------------------

        # Dataframe to format into table
        finetune_df = pd.DataFrame(sql_ret_augmented,
                                    columns=["fine_tune_date", "model_name",
                                            "model_description", "training_data_filename",
                                            "record_count", "model_version",
                                            "deploy_status", "deployment_date", "regression_accuracy", "corrected_accuracy"])
        finetune_dict = finetune_df.to_dict("records")

        return finetune_dict
    
    def get_finetune_state(self):
        # when (ft_lifecycle_state = 'DELETED') then 'deploy'
        select_sql= f"""
            select  workflow_key, training_data_id, model_descr,
            case
                when (config_state = 'set' and dac_submit_time is null) then 'config_set'
                when (config_state = 'cleared') then 'config_start'
                when (dac_lifecycle_state in ('CREATING', 'DELETING', 'UPDATING') 
                     or ft_lifecycle_state in ('CREATING', 'DELETING', 'UPDATING')) then 'finetune'
                when ft_lifecycle_state in ('ACTIVE') and dac_lifecycle_state in ('DELETED') then 'deploy'
                when (deploy_state in ('ignored', 'completed')) then 'config_start'
                else 'config_start'
            end as finetune_state,
            case
                when dac_lifecycle_state in ('CREATING', 'UPDATING') then 'Creating cluster'
                when ft_lifecycle_state in ('CREATING', 'UPDATING') then 'Fine tuning in progress'
                when ft_lifecycle_state in ('ACTIVE') and dac_lifecycle_state in ('DELETED') then 'Fine tuning completed'
                when ft_lifecycle_state in ('ACTIVE') and dac_lifecycle_state in ('DELETING') then 'Deleting cluster'
                else ' '
            end as finetune_status,
            case
                when ft_error_dtls is not null then ft_error_dtls
                when dac_error_dtls is not null then dac_error_dtls
                else ''
            end as error
            from finetune_workflow
            order by id desc
            fetch first 1 row only 
            """
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(select_sql )
                    columns = [col[0].lower() for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        ret= dict(zip(columns, row))
                        logger.info(f"FineTuneWorkflowDAO.get_finetune_state {ret}")
                    else:
                        return None
            
            hist_db: TrainingDataHistoryDAO= TrainingDataHistoryDAO()
            ret["filename"] = hist_db.read_by_id(record_id = ret["training_data_id"])["filename"]
            ret.pop("training_data_id")
            return ret
        except oracledb.Error as e:
            raise Exception(f"Failed to retrieve workflow: {str(e)}")

    def get_evaluate_finetune(self,workflow_key):

        connection = iou.db_get_connection()
        statement = f"""
                    select
                    count (case when eval_category = 'regression' then 1 end) as regression_count,
                    count (case when eval_category = 'regression' and is_accurate = 1 then 1 end) as regression_accurate_count,
                    count (case when eval_category = 'corrected' then 1 end) as corrected_count,
                    count (case when eval_category = 'corrected' and is_accurate = 1 then 1 end) as corrected_accurate_count
                    from finetune_evaluation fe
                    join finetune_workflow fw on finetune_workflow_id = fw.id
                    where workflow_key = '{workflow_key}'
                    """
        result_set = iou.db_select(connection, statement)

        regression_count = result_set[0][0]
        regression_accurate_count = result_set[0][1]
        corrected_count = result_set[0][2]
        corrected_accurate_count = result_set[0][3]

        result_dict = {}
        result_dict["regression_count"] = regression_count
        result_dict["regression_accuracy"] = "NA" if regression_count == 0 else str("{:.3f}".format(regression_accurate_count/regression_count))
        result_dict["corrected_count"] = corrected_count
        result_dict["corrected_accuracy"] = "NA" if corrected_count == 0 else str("{:.3f}".format(corrected_accurate_count/corrected_count))

        logger.info(result_dict)
        connection.close()
        return result_dict

# Example usage:
def test_finetune_workflow():
    dao = FineTuneWorkflowDAO( )
    
    # Create example
    new_workflow = {
        "workflow_key": "FT-20250407-001",
        "training_data_path": "/data/training/dataset1",
        "model_descr": "Fine-tuning for text classification",
        "unit_count": 4,
        "unit_shape": "GENERIC_LARGE",
        "config_state": "set",
        "ft_base_model_id": "ocid-123",
        "ft_life_cycle_state": "created",
        "ft_type": "finetune",
        "ft_version": "1.0",
        "config_submit_time":datetime.datetime.now().strftime(confb.dconfig["metrics"]["python_format"])
        #"dac_created_time":datetime.datetime.now().strftime(confb.dconfig["metrics"]["python_format"]),
        #"dac_started_time":datetime.datetime.now().strftime(confb.dconfig["metrics"]["python_format"]),
        #"ft_created_time":datetime.datetime.now().strftime(confb.dconfig["metrics"]["python_format"]),
        #"ft_completion_time":datetime.datetime.now().strftime(confb.dconfig["metrics"]["python_format"])
    }
    
    try:
        workflow_key = dao.create(new_workflow)
        print(f"Created workflow with key: {workflow_key}")

        # Update example
        update_data = {
            "workflow_key": workflow_key,
            "ft_life_cycle_state": "running",
            "dac_cluster_id": "ocid_cluster-xyz-123"
        }
        
        update_success = dao.update(update_data)
        print(f"Update success: {update_success}")
        
        # Retrieve workflow
        workflow = dao.get_by_key(workflow_key)
        print(f"Retrieved workflow: {workflow}")
        
        # Delete workflow
        delete_success = dao.delete(workflow_key)
        print(f"Delete success: {delete_success}")
        return workflow["id"]
    
    except Exception as e:
        print(f"Error: {str(e)}")

class FineTuneConfigDAO:
    """Data Access Object for FINETUNE_WORKFLOW table operations"""
    
    def create(self, config_data: Dict[str, Any]) -> bool:

        if 'finetune_workflow_id' not in config_data:
            raise ValueError("finetune_workflow_id is required")

        logger.info("FineTuneConfigDAO.create")            
        # Extract all available fields from the dictionary
        workflow_id = config_data.get('finetune_workflow_id')
        early_stopping_patience = config_data.get('early_stopping_patience')
        early_stopping_threshold = config_data.get('early_stopping_threshold')
        learning_rate = config_data.get('learning_rate')
        log_model_metrics_interval = config_data.get('log_model_metrics_interval_in_steps')
        lora_alpha = config_data.get('lora_alpha')
        lora_dropout = config_data.get('lora_dropout')
        lora_r = config_data.get('lora_r')
        total_training_epochs = config_data.get('total_training_epochs')
        training_batch_size = config_data.get('training_batch_size')
        training_config_type = config_data.get('training_config_type')
        
        sql = """
        INSERT INTO FINETUNE_CONFIG (
            FINETUNE_WORKFLOW_ID,
            EARLY_STOPPING_PATIENCE,
            EARLY_STOPPING_THRESHOLD,
            LEARNING_RATE,
            LOG_MODEL_METRICS_INTERVAL_IN_STEPS,
            LORA_ALPHA,
            LORA_DROPOUT,
            LORA_R,
            TOTAL_TRAINING_EPOCHS,
            TRAINING_BATCH_SIZE,
            TRAINING_CONFIG_TYPE
        ) VALUES (
            :workflow_id,
            :early_stopping_patience,
            :early_stopping_threshold,
            :learning_rate,
            :log_model_metrics_interval,
            :lora_alpha,
            :lora_dropout,
            :lora_r,
            :total_training_epochs,
            :training_batch_size,
            :training_config_type
        )
        """
        
        logger.debug(f"FineTuneConfigDAO.create {sql}")            
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, {
                        'workflow_id': workflow_id,
                        'early_stopping_patience': early_stopping_patience,
                        'early_stopping_threshold': early_stopping_threshold,
                        'learning_rate': learning_rate,
                        'log_model_metrics_interval': log_model_metrics_interval,
                        'lora_alpha': lora_alpha,
                        'lora_dropout': lora_dropout,
                        'lora_r': lora_r,
                        'total_training_epochs': total_training_epochs,
                        'training_batch_size': training_batch_size,
                        'training_config_type': training_config_type
                    })
                    connection.commit()
                    return True
        except oracledb.Error as e:
            logger.error(f"Error creating config: {e}")
            return False
    
    def get_by_key(self, finetune_workflow_id: str) -> Optional[Dict[str, Any]]:
        select_sql = "SELECT * FROM FINETUNE_CONFIG WHERE FINETUNE_WORKFLOW_ID = :finetune_workflow_id"
        logger.info("FineTuneConfigDAO.get_by_key-entry")            
        
        try:
            with iou.db_get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(select_sql, {'finetune_workflow_id': finetune_workflow_id})
                    columns = [col[0].lower() for col in cursor.description]
                    row = cursor.fetchone()
                    
                    if row:
                        return dict(zip(columns, row))
                    return None
        except oracledb.Error as e:
            raise Exception(f"Failed to retrieve workflow: {str(e)}")
    
    def update(self, finetune_workflow_id: str, config_data: Dict[str, Any]) -> bool:
        if not config_data:
            return False
        logger.info("FineTuneConfigDAO.update-entry")            

        # Build dynamic update SQL based on provided fields
        update_fields = []
        params = {'finetune_workflow_id': finetune_workflow_id}
        
        for key, value in config_data.items():
            if key != 'finetune_workflow_id':  # Don't update the primary key
                update_fields.append(f"{key.upper()} = :{key}")
                params[key] = value
                
        if not update_fields:
            return False
            
        sql = f"""
                UPDATE FINETUNE_CONFIG 
                SET {', '.join(update_fields)}
                WHERE FINETUNE_WORKFLOW_ID = :finetune_workflow_id
                """
        logger.debug(f"FineTuneConfigDAO: {sql}")
        try:
            with iou.db_get_connection()  as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    if cursor.rowcount > 0:
                        connection.commit()
                        return True
                    return False
        except oracledb.Error as e:
            logger.error(f"Error updating config: {e}")
            return False
    
    def delete(self, finetune_workflow_id: int) -> bool:
        sql = """
            DELETE FROM FINETUNE_CONFIG 
            WHERE FINETUNE_WORKFLOW_ID = :finetune_workflow_id
            """
        logger.info(f"FineTuneConfigDAO.delete {finetune_workflow_id}")            
        
        try:
            with iou.db_get_connection()  as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, {'finetune_workflow_id': finetune_workflow_id})
                    if cursor.rowcount > 0:
                        connection.commit()
                        return True
                    return False
        except oracledb.Error as e:
            logger.error(f"Error deleting config: {e}")
            return False

# Example usage
def test_workflowconfig(id):
    # Example connection parameters - replace with actual values
    
    dao = FineTuneConfigDAO( )
    test_key=id
    # Example: Create a new config
    new_config = {
        'finetune_workflow_id': test_key,
        'early_stopping_patience': 3,
        'early_stopping_threshold': 0.01,
        'learning_rate': 0.0001,
        'log_model_metrics_interval_in_steps': 100,
        'lora_alpha': 16,
        'lora_dropout': 0.1,
        'lora_r': 8,
        'total_training_epochs': 5,
        'training_batch_size': 8,
        'training_config_type': 'default'
    }
    success = dao.create(config_data=new_config)
    print(f"Create result: {success}")
    
    # Example: Read a config
    config = dao.get_by_key(finetune_workflow_id=test_key)
    print(f"Read result: {config}")
    
    # Example: Update a config
    update_data = {
        'LEARNING_RATE': 0.0002,
        'TOTAL_TRAINING_EPOCHS': 10
    }
    success = dao.update(finetune_workflow_id=test_key, config_data=update_data)
    print(f"Update result: {success}")
    
    # Example: Delete a config
    success = dao.delete(finetune_workflow_id=test_key)
    print(f"Delete result: {success}")

class TrainingDataHistoryDAO:
    """Data Access Object for the TRAININGDATA_HISTORY table."""

    def __init__(self):
        """Initialize the DAO."""
        self.table_name = "TRAININGDATA_HISTORY"
        self.columns = ["ID", "RECORD_COUNT", "PATH", "FILENAME", "SUBMIT_TIME", "COMMENTS"]
    
    def create(self, record_count: int, path: str, filename: str, comments: str = None) -> int:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()

            sql = """
                INSERT INTO TRAININGDATA_HISTORY 
                (RECORD_COUNT, PATH, FILENAME, COMMENTS,SUBMIT_TIME) 
                VALUES (:record_count, :path, :filename, :comments, :submit_time) 
                RETURNING ID INTO :new_id
            """
            new_id = cursor.var(oracledb.NUMBER)
            cursor.execute(sql, {
                'record_count': record_count,
                'path': path,
                'filename': filename,
                'comments': comments,
                'new_id': new_id,
                'submit_time': datetime.now()
            })
            connection.commit()
            return new_id.getvalue()
        finally:
            if connection:
                connection.close()
    
    def read_by_id(self, record_id: int) -> Optional[Dict]:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            sql = f"SELECT ID, RECORD_COUNT, PATH, FILENAME, SUBMIT_TIME, COMMENTS FROM {self.table_name} WHERE ID = :id"
            cursor.execute(sql, {'id': record_id})
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'id': row[0],
                'record_count': row[1],
                'path': row[2],
                'filename': row[3],
                'submit_time': row[4],
                'comments': row[5]
            }
        finally:
            if connection:
                connection.close()
    
    def read_all(self,domain,trunc_filename:bool=True) -> List[Dict]:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            if trunc_filename:
                sql = f"""
                        SELECT ID,
                            RECORD_COUNT,
                            PATH,
                            FILENAME,
                            SUBMIT_TIME,
                            COMMENTS
                        FROM {self.table_name}
                        ORDER BY ID"""
            else:
                sql = f"SELECT ID, RECORD_COUNT, PATH, FILENAME, SUBMIT_TIME, COMMENTS FROM {self.table_name} ORDER BY ID"

            cursor.execute(sql)
            
            results = []
            for row in cursor:
                results.append({
                    'id': row[0],
                    'record_count': row[1],
                    'path': row[2],
                    'filename': row[3],
                    'submit_time': row[4],
                    'comments': row[5]
                })
            
            return results
        finally:
            if connection:
                connection.close()
    
    def read_by_filename(self, filename: str) -> List[Dict]:
        logger.info(f"TrainingDataHistoryDAO.read_by_filename::Entry")
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            sql = f"""
                SELECT ID, RECORD_COUNT, PATH, FILENAME, SUBMIT_TIME, COMMENTS 
                FROM {self.table_name} 
                WHERE FILENAME = :filename 
                ORDER BY SUBMIT_TIME DESC
            """
            cursor.execute(sql, {'FILENAME': filename})
            
            results = []
            for row in cursor:
                results.append({
                    'id': row[0],
                    'record_count': row[1],
                    'path': row[2],
                    'filename': row[3],
                    'submit_time': row[4],
                    'comments': row[5]
                })
            logger.info(f"TrainingDataHistoryDAO.read_by_filename {results}")
            if len(results) > 0:
                return results[0]
            else:
                return None
        finally:
            if connection:
                connection.close()
    
    def update(self, record_id: int, record_count: Optional[int] = None, path: Optional[str] = None,
               filename: Optional[str] = None, comments: Optional[str] = None) -> bool:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            
            # Build the SET clause dynamically based on what fields are being updated
            set_clauses = []
            params = {'id': record_id}
            
            if record_count is not None:
                set_clauses.append("RECORD_COUNT = :record_count")
                params['record_count'] = record_count
                
            if path is not None:
                set_clauses.append("PATH = :path")
                params['path'] = path

            if filename is not None:
                set_clauses.append("FILENAME = :filename")
                params['filename'] = filename
                
            if comments is not None:
                set_clauses.append("COMMENTS = :comments")
                params['comments'] = comments
                
            if not set_clauses:
                return False  # Nothing to update
                
            sql = f"""
                UPDATE {self.table_name} 
                SET {', '.join(set_clauses)} 
                WHERE ID = :id
            """
            
            cursor.execute(sql, params)
            connection.commit()
            
            return cursor.rowcount > 0
        finally:
            if connection:
                connection.close()
    
    def delete(self, record_id: int) -> bool:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            sql = f"DELETE FROM {self.table_name} WHERE ID = :id"
            cursor.execute(sql, {'id': record_id})
            connection.commit()
            
            return cursor.rowcount > 0
        finally:
            if connection:
                connection.close()

    def search(self, search_term: str, start_date: Optional[datetime] = None, 
               end_date: Optional[datetime] = None) -> List[Dict]:
        connection = iou.db_get_connection()
        try:
            cursor = connection.cursor()
            
            conditions = []
            params = {}
            
            if search_term:
                conditions.append("(UPPER(FILENAME) LIKE UPPER(:search_term) OR UPPER(COMMENTS) LIKE UPPER(:search_term))")
                params['search_term'] = f"%{search_term}%"
                
            if start_date:
                conditions.append("SUBMIT_TIME >= :start_date")
                params['start_date'] = start_date
                
            if end_date:
                conditions.append("SUBMIT_TIME <= :end_date")
                params['end_date'] = end_date
                
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            sql = f"""
                SELECT ID, RECORD_COUNT, PATH, FILENAME, SUBMIT_TIME, COMMENTS 
                FROM {self.table_name} 
                WHERE {where_clause}
                ORDER BY SUBMIT_TIME DESC
            """
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor:
                results.append({
                    'ID': row[0],
                    'RECORD_COUNT': row[1],
                    'PATH': row[2],
                    'FILENAME': row[3],
                    'SUBMIT_TIME': row[4],
                    'COMMENTS': row[5]
                })
            
            return results
        finally:
            if connection:
                connection.close()


class ModelUsageDAO:

    def create(self, model_usage_data):
        """
        Insert a new record into the MODEL_USAGE table.
        model_usage_data is a dictionary with keys matching table column names.
        """
        sql = """
            INSERT INTO MODEL_USAGE (
                MODEL_PURPOSE,MODEL_NAME,MODEL_SRC,
                USAGE_START,USAGE_STOP,WORKFLOW_ID,
                DAC_CLUSTER_OCID,ENDPOINT_OCID,VERSION
            ) VALUES (
                :MODEL_PURPOSE,
                :MODEL_NAME,
                :MODEL_SRC,
                :USAGE_START,
                :USAGE_STOP,
                :WORKFLOW_ID,
                :DAC_CLUSTER_OCID,
                :ENDPOINT_OCID,
                :VERSION
            )
        """
        
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, model_usage_data)
        self.connection.commit()

    def update(self, model_usage_id, model_usage_data):
        """
        Update an existing record in the MODEL_USAGE table.
        model_usage_id is the primary key (ID).
        model_usage_data is a dictionary with keys matching table column names to be updated.
        """
        model_usage_data.pop("id",None)
        set_clause = ', '.join([f"{key} = :{key}" for key in model_usage_data.keys()])
        sql = f"""
            UPDATE MODEL_USAGE 
            SET {set_clause}
            WHERE ID = :ID
        """
        
        model_usage_data['ID'] = model_usage_id
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        logger.debug(f"ModelUsageDAO.update {model_usage_data}")
        self.cursor.execute(sql, model_usage_data)
        self.connection.commit()

    def delete(self, model_usage_id):
        """
        Delete a record from the MODEL_USAGE table by its primary key ID.
        """
        sql = "DELETE FROM MODEL_USAGE WHERE ID = :ID"
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, {'ID': model_usage_id})
        self.connection.commit()

    def select(self, model_usage_id):
        """
        Select a single record from the MODEL_USAGE table by its primary key ID.
        """
        sql = """SELECT ID,
                    MODEL_PURPOSE,MODEL_NAME,MODEL_SRC,
                    USAGE_START,USAGE_STOP,
                    WORKFLOW_ID,DAC_CLUSTER_OCID,ENDPOINT_OCID,VERSION
                    FROM MODEL_USAGE WHERE ID = :ID
                """
        
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, {'ID': model_usage_id})
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {"id":row[0], "model_purpose":row[1], "model_name":row[2],"model_src":row[3],
                "usage_start":row[4],"usage_stop":row[5],
                "workflow_id":row[6],"dac_cluster_ocid":row[7],"endpoint_ocid":row[8],"version":row[9]}
    
    def select_purpose(self, model_purpose: str):
        """
        Select a single record from the MODEL_USAGE table by its primary key ID.
        """
        sql = """SELECT ID,
                MODEL_PURPOSE,MODEL_NAME,MODEL_SRC,
                USAGE_START,USAGE_STOP,
                WORKFLOW_ID,DAC_CLUSTER_OCID,ENDPOINT_OCID,VERSION
                FROM MODEL_USAGE
                WHERE MODEL_PURPOSE = :MODEL_PURPOSE
                      AND USAGE_STOP is null
                ORDER BY ID DESC
                """
        
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, {'MODEL_PURPOSE': model_purpose})
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {"id":row[0], "model_purpose":row[1], "model_name":row[2],"model_src":row[3],
                "usage_start":row[4],"usage_stop":row[5],"workflow_id":row[6],
                "dac_cluster_ocid":row[7],"endpoint_ocid":row[8],"version":row[9]}

    def select_workflow(self, workflow_id):
        """
        Select a single record from the MODEL_USAGE table by its primary key ID.
        """
        sql = """SELECT ID,
                    MODEL_PURPOSE,MODEL_NAME,MODEL_SRC,
                    USAGE_START,USAGE_STOP,
                    WORKFLOW_ID,DAC_CLUSTER_OCID,ENDPOINT_OCID,VERSION
                FROM MODEL_USAGE WHERE WORKFLOW_ID = :WORKFLOW_ID"""
        
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, {'WORKFLOW_ID': workflow_id})
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {"id":row[0], "model_purpose":row[1], "model_name":row[2],"model_src":row[3],
                "usage_start":row[4],"usage_stop":row[5],
                "workflow_id":row[6],"dac_cluster_ocid":row[7],"endpoint_ocid":row[8],"version":row[9]}

    def read_all(self):
        """
        Select all records from the MODEL_USAGE table.
        """
        sql = """SELECT ID,
                    MODEL_PURPOSE,MODEL_NAME,MODEL_SRC,
                    USAGE_START,USAGE_STOP,
                    WORKFLOW_ID,DAC_CLUSTER_OCID,ENDPOINT_OCID,VERSION
                 FROM MODEL_USAGE"""
        
        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            results.append({"id":row[0], "model_purpose":row[1], "model_name":row[2],"model_src":row[3],
                "usage_start":row[4],"usage_stop":row[5],
                "workflow_id":row[6],"dac_cluster_ocid":row[7],"endpoint_ocid":row[8],"version":row[9]})
            
        return results

    def latest_model(self, model_purpose: str):
        """
        Select most recent records from the MODEL_USAGE table given provided model_purpose.
        """
        sql = """SELECT MODEL_PURPOSE, MAX(USAGE_START) AS LATEST
                FROM MODEL_USAGE WHERE MODEL_PURPOSE = :MODEL_PURPOSE
                GROUP BY MODEL_PURPOSE"""

        self.connection = iou.db_get_connection()
        self.cursor = self.connection.cursor()
        self.cursor.execute(sql, {'MODEL_PURPOSE': model_purpose})
        latest_model_date = self.cursor.fetchone()

        return latest_model_date[1]

    def close(self):
        """
        Close the cursor and connection.
        """
        self.cursor.close()
        self.connection.close()

# Example Usage
def test_model_usage():
    # Establishing a connection to Oracle DB

    dao = ModelUsageDAO( )
    
    # Example of inserting a new record
    new_model_usage = {
        'MODEL_PURPOSE': 'Test Purpose',
        'MODEL_NAME': 'Model1',
        'MODEL_SRC': 'test_source',
        'USAGE_START': datetime(2024, 12, 1),
        'USAGE_STOP': None,
        'WORKFLOW_ID': 666,
        'DAC_CLUSTER_OCID': 'Cluster1',
        'ENDPOINT_OCID': 'Test OCID',
        'VERSION': 'v1.2'
    }
    
    dao.create(new_model_usage)
    
    # Example of selecting a record by ID
    model_usage = dao.select_purpose("Test Purpose")
    logger.debug(model_usage)
    
    # Example of updating a record
    update_data = {
        'DAC_CLUSTER_OCID': 'Updated Cluster1',
        'ENDPOINT_OCID': 'Updated Test OCID'
    }
    dao.update(model_usage["id"], update_data)
    
    # Example of deleting a record
    dao.delete(model_usage["id"])
    
    # Example of reading all records
    all_records = dao.read_all()
    for record in all_records:
        logger.debug(record)

    # Example of getting latest model usage date
    try:
        latest_date = dao.latest_model(constants.MODEL_PURPOSE)
    except TypeError:
        latest_date = confb.dconfig["metrics"]["start_date"]
    logger.debug(latest_date)

    # Close the DAO
    dao.close()
    return model_usage

class FineTuneEvaluationDAO:
    """
    Data Access Object for the FINETUNE_EVALUATION table using zip function
    to map column names with values for easier data manipulation.
    Uses Oracle Database via the oracledb library.
    """
    
    # Define table name and columns as class variables
    TABLE_NAME = "FINETUNE_EVALUATION"
    COLUMNS = [
        "ID", 
        "FINETUNE_WORKFLOW_ID", 
        "EVAL_CATEGORY", 
        "PROMPT_TXT", 
        "SQL_TRUST_LIBARY", 
        "SQL_LLM_GENERATED", 
        "IS_ACCURATE", 
        "LLM_START_TIME", 
        "LLM_END_TIME"
    ]
    
    # Define which columns are required (NOT NULL)
    REQUIRED_COLUMNS = [
        "FINETUNE_WORKFLOW_ID",
        "EVAL_CATEGORY", 
        "IS_ACCURATE"
    ]
        
    def _get_connection(self) -> oracledb.Connection:
        return iou.db_get_connection()
        
    def create(self, data: Dict[str, Any]) -> int:

        data = {k.upper(): v for k, v in data.items()}
        logger.debug(f"finetune_db.FineTuneEvaluationDAO.create {data}")

        # Check required fields
        for required_col in self.REQUIRED_COLUMNS:
            if required_col not in data or data[required_col] is None:
                raise ValueError(f"Required column '{required_col}' is missing or None")
        
        # Use zip to create columns and placeholders for the SQL query
        columns = []
        values = []
        
        for col in self.COLUMNS:
            if col in data and data[col] is not None:
                columns.append(col)
                values.append(data[col])
        
        placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
        columns_str = ", ".join(columns)
        
        insert_sql = f"""
            INSERT INTO {self.TABLE_NAME} ({columns_str})
            VALUES ({placeholders})
            """
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_sql, values)
                conn.commit()
            
        return self.get_next_id()-1
    
    def read_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE ID = :1"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [id])
                row = cursor.fetchone()
                
                if row is None:
                    return None
                
                # Get column names from cursor description
                column_names = [col[0] for col in cursor.description]
                
                # Use zip to map column names to values
                return dict(zip(column_names, row))
    
    def read_by_workflow_id(self, workflow_id: int) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE FINETUNE_WORKFLOW_ID = :1"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [workflow_id])
                rows = cursor.fetchall()
                
                # Get column names from cursor description
                column_names = [col[0] for col in cursor.description]
                
                # Use zip to map column names to values for each row
                return [dict(zip(column_names, row)) for row in rows]
    
    def read_all(self) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.TABLE_NAME}"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Get column names from cursor description
                column_names = [col[0] for col in cursor.description]
                
                # Use zip to map column names to values for each row
                return [dict(zip(column_names, row)) for row in rows]
    
    def update(self, id: int, data: Dict[str, Any]) -> bool:
        # Check that we're not setting required fields to None
        for required_col in self.REQUIRED_COLUMNS:
            if required_col in data and data[required_col] is None:
                raise ValueError(f"Required column '{required_col}' cannot be set to None")
        
        # Filter out ID from the update data (since it's the primary key)
        update_data = {k: v for k, v in data.items() if k != "ID" and k in self.COLUMNS}
        
        if not update_data:
            return False  # Nothing to update
        
        # Use zip to create SET clause parts
        set_clauses = []
        values = []
        
        for i, (column, value) in enumerate(update_data.items(), start=1):
            set_clauses.append(f"{column} = :{i}")
            values.append(value)
        
        # Add the ID to the values
        values.append(id)
        
        update_sql = f""" UPDATE {self.TABLE_NAME}
                SET {', '.join(set_clauses)}
                WHERE ID = :{len(values)}
                """
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(update_sql, values)
                rows_updated = cursor.rowcount
                conn.commit()
                
                # Return True if a row was updated
                return rows_updated > 0
    
    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE EVAL_CATEGORY = :1"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [category])
                rows = cursor.fetchall()
                
                # Get column names from cursor description
                column_names = [col[0] for col in cursor.description]
                
                # Use zip to map column names to values for each row
                return [dict(zip(column_names, row)) for row in rows]
    
    def find_by_accuracy(self, is_accurate: bool) -> List[Dict[str, Any]]:
        # Convert boolean to numeric (1 or 0)
        is_accurate_num = 1 if is_accurate else 0
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE IS_ACCURATE = :1"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [is_accurate_num])
                rows = cursor.fetchall()
                
                # Get column names from cursor description
                column_names = [col[0] for col in cursor.description]
                
                # Use zip to map column names to values for each row
                return [dict(zip(column_names, row)) for row in rows]
    
    def delete(self, id: int) -> bool:
        delete_sql = f"DELETE FROM {self.TABLE_NAME} WHERE ID = :1"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(delete_sql, [id])
                rows_deleted = cursor.rowcount
                conn.commit()
                
                # Return True if a row was deleted
                return rows_deleted > 0
    
    def get_next_id(self) -> int:
        query = f"SELECT NVL(MAX(ID), 0) + 1 FROM {self.TABLE_NAME}"
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()[0]


# Example usage
def test_finetune_evaluation():

    dao = FineTuneEvaluationDAO( )
    
    # Example of creating a record
    next_id = dao.get_next_id()
    new_evaluation = {
        "FINETUNE_WORKFLOW_ID": 101,
        "EVAL_CATEGORY": "SQL Generation",
        "PROMPT_TXT": "Generate a query to find all users who registered last month",
        "SQL_TRUST_LIBARY": "SELECT * FROM users WHERE registration_date BETWEEN TO_DATE('2023-03-01', 'YYYY-MM-DD') AND TO_DATE('2023-03-31', 'YYYY-MM-DD')",
        "SQL_LLM_GENERATED": "SELECT * FROM users WHERE EXTRACT(MONTH FROM registration_date) = EXTRACT(MONTH FROM SYSDATE - INTERVAL '1' MONTH)",
        "IS_ACCURATE": 1,
        "LLM_START_TIME": datetime.now(),
        "LLM_END_TIME": datetime.now()
    }
    
    try:
        dao.create(new_evaluation)
        print(f"Created evaluation with ID: {next_id-1}")
        evaluation = dao.read_by_id(next_id-1)
        print(f"Read evaluation: {evaluation}")
        update_data = {
            "IS_ACCURATE": 0,
            "SQL_LLM_GENERATED": "SELECT * FROM users WHERE TRUNC(registration_date, 'MM') = TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM')"
        }
        
        dao.update(next_id-1, update_data)
        print("Updated evaluation")
        updated_evaluation = dao.read_by_id(next_id-1)
        print(f"Updated evaluation: {updated_evaluation}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_trainingdata_history():
    dao: TrainingDataHistoryDAO = TrainingDataHistoryDAO()
    dao.create(record_count=10, path="/somewhere/something/", filename='somefile',comments='testing')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    confb.setup()
    #id=test_finetune_workflow()
    #test_workflowconfig(id)
    #test_trainingdata_history()
    test_model_usage()
    #test_finetune_evaluation()