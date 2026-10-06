-- ====================================================================
-- ГЛАВА 3: БИЗНЕС-ЛОГИКА И РАСЧЕТ XP (ИСПРАВЛЕННЫЙ TASK_TYPE)
-- ====================================================================
DO $$
DECLARE
    v_role_id INT;
    v_level_id INT;
    v_mission_id INT;
    v_task_id INT;
    v_user_id INT;
    v_initial_xp INT;
    v_xp_after_first INT;
    v_xp_after_second INT;
    v_is_mission_completed BOOLEAN;
    v_completion_count INT;
BEGIN
    RAISE NOTICE '=== НАЧАЛО ТЕСТИРОВАНИЯ БИЗНЕС-ЛОГИКИ ===';

    -- 1. Подготовка фикстур (тестовых сущностей)
    INSERT INTO roles (name) VALUES ('logic_test_role') RETURNING id INTO v_role_id;
    INSERT INTO levels (code, title) VALUES ('L1', 'Logic Level') RETURNING id INTO v_level_id;
    INSERT INTO missions (level_id, order_index, title) VALUES (v_level_id, 1, 'Logic Mission') RETURNING id INTO v_mission_id;
    
    -- Использовано проверенное значение 'vocabulary_game'
    INSERT INTO tasks (mission_id, title, task_type, xp_reward_first, xp_reward_repeat, order_number)
    VALUES (v_mission_id, 'Grammar Task', 'vocabulary_game', 100, 20, 1) 
    RETURNING id INTO v_task_id;

    -- Пользователь с начальным 0 XP
    INSERT INTO users (first_name, last_name, email, password_hash, role_id, cefr_level, total_xp)
    VALUES ('Logic', 'Tester', 'logic_test@user.com', 'hash', v_role_id, 'A1', 0) 
    RETURNING id, total_xp INTO v_user_id, v_initial_xp;


    -- 2. ТЕСТ: Проверка инициализации пользователя
    IF v_initial_xp = 0 THEN
        RAISE NOTICE 'ПРОЙДЕН [1/4]: Стартовый XP пользователя корректно равен 0!';
    ELSE
        RAISE EXCEPTION 'ПОВАЛЕН: Стартовый XP равен % вместо 0', v_initial_xp;
    END IF;


    -- 3. ТЕСТ: Первичное прохождение этапов и запись прогресса
    INSERT INTO user_mission_progress (
        user_id, 
        mission_id, 
        is_completed, 
        tests_passed, 
        pronunciation_passed, 
        best_score_percentage, 
        completion_count, 
        last_completed_at
    )
    VALUES (
        v_user_id, 
        v_mission_id, 
        false, 
        true,   -- Тест пройден
        false,  -- Произношение еще не пройдено
        85.5,   -- Процент прохождения мини-игры
        0,      -- Количество полных прохождений миссии
        NULL    -- Дата завершения пока NULL
    );

    -- Начисление XP за первое выполнение
    UPDATE users 
    SET total_xp = total_xp + (SELECT xp_reward_first FROM tasks WHERE id = v_task_id)
    WHERE id = v_user_id
    RETURNING total_xp INTO v_xp_after_first;

    IF v_xp_after_first = 100 THEN
        RAISE NOTICE 'ПРОЙДЕН [2/4]: Первичное прохождение задачи начислило 100 XP!';
    ELSE
        RAISE EXCEPTION 'ПОВАЛЕН: Неверный XP за первое прохождение: %', v_xp_after_first;
    END IF;


    -- 4. ТЕСТ: Повторное прохождение задачи
    UPDATE users 
    SET total_xp = total_xp + (SELECT xp_reward_repeat FROM tasks WHERE id = v_task_id)
    WHERE id = v_user_id
    RETURNING total_xp INTO v_xp_after_second;

    IF v_xp_after_second = 120 THEN
        RAISE NOTICE 'ПРОЙДЕН [3/4]: Повторное прохождение корректно прибавило 20 XP (Итого: 120 XP)!';
    ELSE
        RAISE EXCEPTION 'ПОВАЛЕН: Неверный XP за повторное прохождение: %', v_xp_after_second;
    END IF;


    -- 5. ТЕСТ: Полное завершение миссии
    UPDATE user_mission_progress
    SET 
        pronunciation_passed = true,
        best_score_percentage = 100.0,
        is_completed = true,
        completion_count = completion_count + 1,
        last_completed_at = NOW()
    WHERE user_id = v_user_id AND mission_id = v_mission_id
    RETURNING is_completed, completion_count INTO v_is_mission_completed, v_completion_count;

    IF v_is_mission_completed = true AND v_completion_count = 1 THEN
        RAISE NOTICE 'ПРОЙДЕН [4/4]: Миссия успешно завершена! (is_completed = true, completion_count = 1)';
    ELSE
        RAISE EXCEPTION 'ПОВАЛЕН: Ошибка при обновлении завершения миссии!';
    END IF;


    -- Откат транзакции для сохранения чистоты базы данных
    RAISE EXCEPTION USING ERRCODE = 'USER0', MESSAGE = 'ТЕСТЫ БИЗНЕС-ЛОГИКИ ЗАВЕРШЕНЫ УСПЕШНО';

EXCEPTION WHEN SQLSTATE 'USER0' THEN
    RAISE NOTICE '=== ВСЕ ТЕСТЫ БИЗНЕС-ЛОГИКИ УСПЕШНО ПРОЙДЕНЫ ===';
END $$;