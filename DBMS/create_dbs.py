# DataPreprocessLogics/DBMS/create_dbs.py

from psycopg2.extras import execute_values
from psycopg2 import sql
import psycopg2
import yaml
import re

def get_connection(config_path="run_config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    print(config)

    return psycopg2.connect(
        host=config['db']['host'],     # docker-compose 사용 시 service name
        port=config['db']['port'],          # PostgreSQL 포트 (docker-compose.yml 확인)
        dbname=config['db']['dbname'],     # DB 이름
        user=config['db']['user'],     # 사용자
        password=config['db']['password']  # 비밀번호
    )


### TODO : 기존에 DB 테이블 생성하는 함수 모두 정리해서 올리기 ###
def create_dictionary_tables(conn):
    cursor = conn.cursor()
    for table in ["개인정보", "준식별자", "기밀정보"]:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                단어 TEXT,
                부서명 TEXT,
                문서명 TEXT,
                단어유형 TEXT,
                구분 TEXT
            );
        """)
    conn.commit()
    cursor.close()

# # 각 단계별 검증 지표가 저장될 친구들, 인데 각 단계별 sent_dataset_log 테이블에서 사용하는데 지워도 되겠지?
# def create_metric_tables(conn):
#     cursor = conn.cursor()
#     for table in ["모델_개인", "모델_기밀", "검증1_개인", "검증2_개인", "검증3_개인", "검증1_기밀", "검증2_기밀", "검증3_기밀"]:
#         cursor.execute(f"""
#             CREATE TABLE IF NOT EXISTS {table} (
#                 test_name TEXT,
#                 timestamp TEXT,
#                 m_0_0 TEXT,
#                 m_0_1 TEXT,
#                 m_0_2 TEXT,
#                 m_1_0 TEXT,
#                 m_1_1 TEXT,
#                 m_1_2 TEXT,
#                 m_2_0 TEXT,
#                 m_2_1 TEXT,
#                 m_2_2 TEXT
#             );
#         """)
#     conn.commit()
#     cursor.close()


# # 각 단계별 sent_dataset_log 테이블에서 사용하는데 지워도 되겠지?
# def create_prediction_tables(conn):
#     cursor = conn.cursor()
#     for table in ["pii_prediction", "confid_prediction"]:
#         cursor.execute(f"""
#             CREATE TABLE IF NOT EXISTS {table} (
#                 test_name TEXT,
#                 timestamp TEXT,
#                 단어 TEXT,
#                 prediction_level TEXT,
#                 ground_truth TEXT,
#                 prediction TEXT
#             );
#         """)
#     conn.commit()
#     cursor.close()


# def create_manual_validation_tables(conn):
#     cursor = conn.cursor()
#     for table in ["pii_validation", "confid_validation"]:
#         cursor.execute(f"""
#             CREATE TABLE IF NOT EXISTS {table} (
#                 test_name TEXT,
#                 timestamp TEXT,
#                 generated_sent TEXT,
#                 단어 TEXT,
#                 generation_target_label TEXT,
#                 validated_label TEXT
#             );
#         """)
#     conn.commit()
#     cursor.close()

### ------------------------------------------------------ ###

def create_exp_log_tables(conn):
    # 실험로그 테이블 스키마 설명 관련하여 아래 링크를 참조하시기 바랍니다.
    # https://oil-jacket-765.notion.site/DB-2720c798efff80728305ec4ba23bfce9?source=copy_link

    cursor = conn.cursor()

    # 실험소요시간(실험 총 개요) scheme
    table_name = "experiment"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT PRIMARY KEY,
            previous_experiment_name TEXT,
            experiment_start_time TEXT,
            experiment_end_time TEXT,
            model_train_duration TEXT,
            validation_1_duration TEXT,
            validation_2_duration TEXT,
            validation_3_duration TEXT,
            aug_sent_generation_duration TEXT,
            aug_sent_auto_valid_duration TEXT,
            aug_sent_manual_valid_duration TEXT,
            total_document_counts TEXT,
            total_sentence_counts TEXT,
            total_annotation_counts TEXT
        );
    """)

    # 모델학습 성능표 scheme
    table_name = "model_train_performance"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT PRIMARY KEY,
            model_train_start_time TEXT,
            model_train_end_time TEXT,
            model_weight_file_path TEXT,
            best_performed_epoch TEXT,
            best_precision TEXT,
            best_recall TEXT,
            best_micro_f1 TEXT,
            best_confusion_matrix TEXT,
            CONSTRAINT fk_experiment_model_train_performance
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 모델학습 데이터셋 문장 별 로그 scheme
    table_name = "model_train_sent_dataset_log"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT,
            sentence_id TEXT,
            validated_epoch TEXT,
            sentence TEXT,
            span_text TEXT,
            index_in_dataset_class TEXT,
            ground_truth TEXT,
            prediction TEXT,
            source_file_name TEXT,
            sentence_sequence_in_source_file TEXT,
            CONSTRAINT fk_experiment_model_train_sent_dataset_log
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증1단계 성능표 scheme
    table_name = "validation_1_performance"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT PRIMARY KEY,
            validation_1_start_time TEXT,
            validation_1_end_time TEXT,
            hit_counts TEXT,
            hit_delta_rate TEXT,
            wrong_counts TEXT,
            wrong_delta_rate TEXT,
            mismatch_counts TEXT,
            mismatch_delta_rate TEXT,
            dictionary_size TEXT,
            dictionary_size_delta_rate TEXT,
            confusion_matrix TEXT,
            CONSTRAINT fk_experiment_validation_1_performance
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증1단계 데이터셋 문장 별 로그 scheme
    table_name = "validation_1_sent_dataset_log"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT,
            sentence_id TEXT,
            sentence TEXT,
            span_text TEXT,
            index_in_dataset_class TEXT,
            ground_truth TEXT,
            prediction TEXT,
            source_file_name TEXT,
            sentence_sequence_in_source_file TEXT,
            CONSTRAINT fk_experiment_validation_1_sent_dataset_log
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증2단계 성능표 scheme
    table_name = "validation_2_performance"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT PRIMARY KEY,
            validation_2_start_time TEXT,
            validation_2_end_time TEXT,
            hit_counts TEXT,
            hit_delta_rate TEXT,
            wrong_counts TEXT,
            wrong_delta_rate TEXT,
            mismatch_counts TEXT,
            mismatch_delta_rate TEXT,
            confusion_matrix TEXT,
            CONSTRAINT fk_experiment_validation_2_performance
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증2단계 데이터셋 문장 별 로그 scheme
    table_name = "validation_2_sent_dataset_log"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT,
            sentence_id TEXT,
            sentence TEXT,
            span_text TEXT,
            index_in_dataset_class TEXT,
            ground_truth TEXT,
            prediction TEXT,
            source_file_name TEXT,
            sentence_sequence_in_source_file TEXT,
            CONSTRAINT fk_experiment_validation_2_sent_dataset_log
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증3단계 성능표 scheme
    table_name = "validation_3_performance"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT PRIMARY KEY,
            validation_3_start_time TEXT,
            validation_3_end_time TEXT,
            model_weight_file_path TEXT,
            precision TEXT,
            recall TEXT,
            f1 TEXT,
            confusion_matrix TEXT,
            CONSTRAINT fk_experiment_validation_3_performance
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # 검증3단계 데이터셋 문장 별 로그 scheme
    table_name = "validation_3_sent_dataset_log"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT,
            sentence_id TEXT,
            sentence TEXT,
            span_text TEXT,
            index_in_dataset_class TEXT,
            ground_truth TEXT,
            prediction TEXT,
            source_file_name TEXT,
            sentence_sequence_in_source_file TEXT,
            CONSTRAINT fk_experiment_validation_3_sent_dataset_log
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    # GPT 문장 생성 데이터셋 별 로그 scheme
    table_name = 'augmented_generation_sent_dataset_log'
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            experiment_name TEXT,
            sentence_id TEXT PRIMARY KEY,
            generated_sentence TEXT,
            span_text TEXT,
            target_ground_truth TEXT,
            validated_label TEXT,
            valid_sentences_counts TEXT,
            invalid_sentences_counts TEXT,
            source_file_name TEXT,
            CONSTRAINT fk_experiment_augmented_generation_sent_dataset_log
                FOREIGN KEY (experiment_name)
                REFERENCES experiment (experiment_name)
                ON DELETE CASCADE
        );
    """)

    conn.commit()
    cursor.close()


if __name__ == "__main__":
    file_path = input("\n[Insert Absolute Path of Config]\nEmpty for default path: 'run_config.yaml'\n-> ")
    if file_path:
        conn = get_connection(config_path=file_path)
    else:
        conn = get_connection()

    create_dictionary_tables(conn)
    # create_metric_tables(conn)
    # create_prediction_tables(conn)
    # create_manual_validation_tables(conn)
    create_exp_log_tables(conn)

    conn.close()