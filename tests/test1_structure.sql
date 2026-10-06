DO $$
DECLARE
    v_role_id INT;
    v_level_id INT;
    v_mission_id INT;
BEGIN
    RAISE NOTICE '=== НАЧАЛО ТЕСТИРОВАНИЯ СТРУКТУРЫ ===';

    -- Подготовка необходимых зависимостей (роль, уровень и миссия)
    INSERT INTO roles (name) VALUES ('test_fixture_role') 
    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name 
    RETURNING id INTO v_role_id;

    INSERT INTO levels (code, title) VALUES ('T1', 'Test Level') 
    ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title 
    RETURNING id INTO v_level_id;

    INSERT INTO missions (level_id, order_index, title) VALUES (v_level_id, 5, 'Fixture Mission')
    ON CONFLICT (level_id, order_index) DO UPDATE SET title = EXCLUDED.title
    RETURNING id INTO v_mission_id;


    -- 1. ТЕСТ: UNIQUE на roles.name
    BEGIN
        INSERT INTO roles (name) VALUES ('test_student_role');
        INSERT INTO roles (name) VALUES ('test_student_role');
        RAISE EXCEPTION 'ПОВАЛЕН: roles.name разрешил дубликат!';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [1/6]: UNIQUE на roles.name работает!';
    END;


    -- 2. ТЕСТ: UNIQUE на (level_id, order_index) в missions
    BEGIN
        INSERT INTO missions (level_id, order_index, title) VALUES (v_level_id, 1, 'M1');
        INSERT INTO missions (level_id, order_index, title) VALUES (v_level_id, 1, 'M2');
        RAISE EXCEPTION 'ПОВАЛЕН: missions разрешил дубликат (level_id, order_index)!';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [2/6]: UNIQUE на (level_id, order_index) работает!';
    END;


    -- 3. ТЕСТ: NOT NULL на users.email
    BEGIN
        INSERT INTO users (first_name, last_name, email, password_hash, role_id) 
        VALUES ('John', 'Doe', NULL, 'hash123', v_role_id);
        RAISE EXCEPTION 'ПОВАЛЕН: users разрешил NULL в email!';
    EXCEPTION WHEN not_null_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [3/6]: NOT NULL на users.email работает!';
    END;


    -- 4. ТЕСТ: CHECK на users.cefr_level
    BEGIN
        INSERT INTO users (first_name, last_name, email, password_hash, cefr_level, role_id)
        VALUES ('Test', 'User', 'test_cefr@user.com', 'pass', 'B3', v_role_id);
        RAISE EXCEPTION 'ПОВАЛЕН: users.cefr_level разрешил уровень B3!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [4/6]: CHECK на users.cefr_level работает!';
    END;


    -- 5. ТЕСТ: CHECK на tasks.xp_reward_first (передаем task_type и xp_reward_repeat)
    BEGIN
        INSERT INTO tasks (mission_id, title, task_type, xp_reward_first, xp_reward_repeat, order_number) 
        VALUES (v_mission_id, 'Invalid XP', 'vocabulary_game', 0, 10, 1);
        RAISE EXCEPTION 'ПОВАЛЕН: tasks.xp_reward_first разрешил 0 XP!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [5/6]: CHECK на tasks.xp_reward_first работает!';
    END;


    -- 6. ТЕСТ: CHECK на calibration_questions.correct_option
    BEGIN
        INSERT INTO calibration_questions (question_text, cefr_level, option_a, option_b, option_c, option_d, correct_option)
        VALUES ('Q', 'A1', 'a', 'b', 'c', 'd', 'X');
        RAISE EXCEPTION 'ПОВАЛЕН: correct_option разрешил букву X!';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [6/6]: CHECK на correct_option работает!';
    END;


    -- Безопасный откат всех данных
    RAISE EXCEPTION USING ERRCODE = 'USER0', MESSAGE = 'ТЕСТЫ ЗАВЕРШЕНЫ УСПЕШНО';

EXCEPTION WHEN SQLSTATE 'USER0' THEN
    RAISE NOTICE '=== ВСЕ ТЕСТЫ СТРУКТУРЫ УСПЕШНО ПРОЙДЕНЫ ===';
END $$;