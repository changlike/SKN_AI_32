-- root 또는 CREATE USER/GRANT 권한이 있는 MySQL 계정으로 실행합니다.
-- 실습용 데이터베이스가 이미 존재하면 삭제하지 않고 그대로 사용합니다.
CREATE DATABASE IF NOT EXISTS django_member_board
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- localhost에서 접속하는 Django 전용 계정을 생성합니다.
CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'django1234!';
-- 127.0.0.1로 접속하는 환경도 고려하여 동일 사용자 계정을 생성합니다.
CREATE USER IF NOT EXISTS 'django_user'@'127.0.0.1' IDENTIFIED BY 'django1234!';

-- 프로젝트 DB의 모든 테이블에 대한 권한을 localhost 계정에 부여합니다.
GRANT ALL PRIVILEGES ON django_member_board.* TO 'django_user'@'localhost';
-- 프로젝트 DB의 모든 테이블에 대한 권한을 127.0.0.1 계정에 부여합니다.
GRANT ALL PRIVILEGES ON django_member_board.* TO 'django_user'@'127.0.0.1';
-- 권한 변경 내용을 즉시 반영합니다.
FLUSH PRIVILEGES;
