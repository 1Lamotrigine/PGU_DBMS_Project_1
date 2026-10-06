DO $$
DECLARE
    v_role_id INT;
    v_level_id INT;
    v_mission_id INT;
    v_task_id INT;
    v_user_id INT;
    v_task_count INT;
BEGIN
    RAISE NOTICE '=== НАЧАЛО ТЕСТИРОВАНИЯ ССЫЛОЧНОЙ ЦЕЛОСТНОСТИ (FK & CASCADE) ===';

    -- 1. Подготовка тестовых данных
    INSERT INTO roles (name) VALUES ('fk_test_role') RETURNING id INTO v_role_id;
    INSERT INTO levels (code, title) VALUES ('FK1', 'FK Level') RETURNING id INTO v_level_id;
    
    INSERT INTO missions (level_id, order_index, title) 
    VALUES (v_level_id, 1, 'FK Mission') 
    RETURNING id INTO v_mission_id;

    INSERT INTO tasks (mission_id, title, task_type, xp_reward_first, xp_reward_repeat, order_number)
    VALUES (v_mission_id, 'FK Task', 'vocabulary_game', 50, 10, 1)
    RETURNING id INTO v_task_id;

    -- Передаем обязательное поле cefr_level
    INSERT INTO users (first_name, last_name, email, password_hash, role_id, cefr_level)
    VALUES ('FK', 'User', 'fk_test@user.com', 'hash', v_role_id, 'A1')
    RETURNING id INTO v_user_id;

    -- 2. ТЕСТ: RESTRICT / NO ACTION на roles (Нельзя удалить роль, пока есть пользователь)
    BEGIN
        DELETE FROM roles WHERE id = v_role_id;
        RAISE EXCEPTION 'ПОВАЛЕН: Блокировка FK на roles не сработала!';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'ПРОЙДЕН [1/2]: RESTRICT на roles работает (пользователь защищает роль)!';
    END;

    -- 3. ТЕСТ: CASCADE на missions -> tasks (Удаление миссии должно удалить её задачи)
    DELETE FROM missions WHERE id = v_mission_id;
    SELECT COUNT(*) INTO v_task_count FROM tasks WHERE id = v_task_id;
    
    IF v_task_count = 0 THEN
        RAISE NOTICE 'ПРОЙДЕН [2/2]: ON DELETE CASCADE на missions -> tasks работает!';
    ELSE
        RAISE EXCEPTION 'ПОВАЛЕН: Задача осталась в БД после удаления миссии!';
    END IF;

    -- Безопасный откат всех созданных данных
    RAISE EXCEPTION USING ERRCODE = 'USER0', MESSAGE = 'ТЕСТЫ ССЫЛОЧНОЙ ЦЕЛОСТНОСТИ ЗАВЕРШЕНЫ УСПЕШНО';

EXCEPTION WHEN SQLSTATE 'USER0' THEN
    RAISE NOTICE '=== ВСЕ ТЕСТЫ ССЫЛОЧНОЙ ЦЕЛОСТНОСТИ УСПЕШНО ПРОЙДЕНЫ ===';
END $$;