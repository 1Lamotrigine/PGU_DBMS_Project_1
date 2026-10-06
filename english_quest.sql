--
-- PostgreSQL database dump
--

\restrict qfqwGClDi31roJyuswaqzohKBDO6PZI9XQDJ2THlpXgCr2n6j19HeeCm9EZ0x7y

-- Dumped from database version 18.3 (Homebrew)
-- Dumped by pg_dump version 18.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.vocabulary_items DROP CONSTRAINT IF EXISTS vocabulary_items_level_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_role_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_level_id_fkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_group_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_mission_progress DROP CONSTRAINT IF EXISTS user_mission_progress_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_mission_progress DROP CONSTRAINT IF EXISTS user_mission_progress_mission_id_fkey;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_mission_id_fkey;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_task_id_fkey;
ALTER TABLE IF EXISTS ONLY public.question_options DROP CONSTRAINT IF EXISTS question_options_question_id_fkey;
ALTER TABLE IF EXISTS ONLY public.missions DROP CONSTRAINT IF EXISTS missions_level_id_fkey;
ALTER TABLE IF EXISTS ONLY public.vocabulary_items DROP CONSTRAINT IF EXISTS vocabulary_items_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.user_mission_progress DROP CONSTRAINT IF EXISTS user_mission_progress_pkey;
ALTER TABLE IF EXISTS ONLY public.user_mission_progress DROP CONSTRAINT IF EXISTS uq_progress_user_mission;
ALTER TABLE IF EXISTS ONLY public.missions DROP CONSTRAINT IF EXISTS uq_missions_level_order;
ALTER TABLE IF EXISTS ONLY public.tasks DROP CONSTRAINT IF EXISTS tasks_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_name_key;
ALTER TABLE IF EXISTS ONLY public.questions DROP CONSTRAINT IF EXISTS questions_pkey;
ALTER TABLE IF EXISTS ONLY public.question_options DROP CONSTRAINT IF EXISTS question_options_pkey;
ALTER TABLE IF EXISTS ONLY public.missions DROP CONSTRAINT IF EXISTS missions_pkey;
ALTER TABLE IF EXISTS ONLY public.levels DROP CONSTRAINT IF EXISTS levels_pkey;
ALTER TABLE IF EXISTS ONLY public.levels DROP CONSTRAINT IF EXISTS levels_code_key;
ALTER TABLE IF EXISTS ONLY public.groups DROP CONSTRAINT IF EXISTS groups_pkey;
ALTER TABLE IF EXISTS ONLY public.calibration_questions DROP CONSTRAINT IF EXISTS calibration_questions_pkey;
ALTER TABLE IF EXISTS public.vocabulary_items ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_mission_progress ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.tasks ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.roles ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.questions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.question_options ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.missions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.levels ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.groups ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.calibration_questions ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.vocabulary_items_id_seq;
DROP TABLE IF EXISTS public.vocabulary_items;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.user_mission_progress_id_seq;
DROP TABLE IF EXISTS public.user_mission_progress;
DROP SEQUENCE IF EXISTS public.tasks_id_seq;
DROP TABLE IF EXISTS public.tasks;
DROP SEQUENCE IF EXISTS public.roles_id_seq;
DROP TABLE IF EXISTS public.roles;
DROP SEQUENCE IF EXISTS public.questions_id_seq;
DROP TABLE IF EXISTS public.questions;
DROP SEQUENCE IF EXISTS public.question_options_id_seq;
DROP TABLE IF EXISTS public.question_options;
DROP SEQUENCE IF EXISTS public.missions_id_seq;
DROP TABLE IF EXISTS public.missions;
DROP SEQUENCE IF EXISTS public.levels_id_seq;
DROP TABLE IF EXISTS public.levels;
DROP SEQUENCE IF EXISTS public.groups_id_seq;
DROP TABLE IF EXISTS public.groups;
DROP SEQUENCE IF EXISTS public.calibration_questions_id_seq;
DROP TABLE IF EXISTS public.calibration_questions;
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: calibration_questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calibration_questions (
    id integer NOT NULL,
    question_text text NOT NULL,
    cefr_level character varying(5) NOT NULL,
    option_a character varying(255) NOT NULL,
    option_b character varying(255) NOT NULL,
    option_c character varying(255) NOT NULL,
    option_d character varying(255) NOT NULL,
    correct_option character varying(1) NOT NULL,
    CONSTRAINT ck_calib_cefr_level CHECK (((cefr_level)::text = ANY ((ARRAY['A1'::character varying, 'A2'::character varying, 'B1'::character varying, 'B2'::character varying, 'C1'::character varying, 'C2'::character varying])::text[]))),
    CONSTRAINT ck_calib_correct_option CHECK (((correct_option)::text = ANY ((ARRAY['A'::character varying, 'B'::character varying, 'C'::character varying, 'D'::character varying])::text[])))
);


--
-- Name: calibration_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.calibration_questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: calibration_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.calibration_questions_id_seq OWNED BY public.calibration_questions.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: levels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.levels (
    id integer NOT NULL,
    code character varying(5) NOT NULL,
    title character varying(100)
);


--
-- Name: levels_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.levels_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: levels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.levels_id_seq OWNED BY public.levels.id;


--
-- Name: missions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.missions (
    id integer NOT NULL,
    level_id integer NOT NULL,
    order_index integer NOT NULL,
    title character varying(255),
    description text,
    is_active boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_missions_order_index CHECK (((order_index >= 1) AND (order_index <= 5)))
);


--
-- Name: missions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.missions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: missions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.missions_id_seq OWNED BY public.missions.id;


--
-- Name: question_options; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.question_options (
    id integer NOT NULL,
    question_id integer NOT NULL,
    option_text text NOT NULL,
    translation_ru character varying(255),
    is_correct boolean NOT NULL,
    image_url character varying(500)
);


--
-- Name: question_options_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.question_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: question_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.question_options_id_seq OWNED BY public.question_options.id;


--
-- Name: questions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.questions (
    id integer NOT NULL,
    task_id integer NOT NULL,
    question_text text NOT NULL,
    question_type character varying(30) NOT NULL,
    CONSTRAINT ck_questions_question_type CHECK (((question_type)::text = ANY ((ARRAY['multiple_choice'::character varying, 'fill_blank'::character varying, 'translation'::character varying, 'image_match'::character varying])::text[])))
);


--
-- Name: questions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.questions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.questions_id_seq OWNED BY public.questions.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    mission_id integer NOT NULL,
    title character varying(255),
    description text,
    task_type character varying(50) NOT NULL,
    order_number integer NOT NULL,
    time_limit integer,
    xp_reward_first integer NOT NULL,
    xp_reward_repeat integer NOT NULL,
    CONSTRAINT ck_tasks_task_type CHECK (((task_type)::text = ANY ((ARRAY['vocabulary_game'::character varying, 'multiple_choice'::character varying, 'translation'::character varying])::text[]))),
    CONSTRAINT ck_tasks_xp_first CHECK ((xp_reward_first > 0)),
    CONSTRAINT ck_tasks_xp_repeat CHECK ((xp_reward_repeat >= 0))
);


--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: user_mission_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_mission_progress (
    id integer NOT NULL,
    user_id integer NOT NULL,
    mission_id integer NOT NULL,
    is_completed boolean NOT NULL,
    tests_passed boolean DEFAULT false NOT NULL,
    pronunciation_passed boolean DEFAULT false NOT NULL,
    best_score_percentage double precision DEFAULT 0.0 NOT NULL,
    completion_count integer DEFAULT 0 NOT NULL,
    last_completed_at timestamp without time zone
);


--
-- Name: user_mission_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_mission_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_mission_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_mission_progress_id_seq OWNED BY public.user_mission_progress.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    cefr_level character varying(5) NOT NULL,
    level_id integer,
    total_xp integer DEFAULT 0 NOT NULL,
    is_calibrated boolean DEFAULT false NOT NULL,
    role_id integer NOT NULL,
    group_id integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_users_cefr_level CHECK (((cefr_level)::text = ANY ((ARRAY['A1'::character varying, 'A2'::character varying, 'B1'::character varying, 'B2'::character varying, 'C1'::character varying, 'C2'::character varying])::text[])))
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vocabulary_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vocabulary_items (
    id integer NOT NULL,
    level_id integer NOT NULL,
    word_en character varying(255) NOT NULL,
    word_ru character varying(255) NOT NULL,
    transcription character varying(255),
    image_url character varying(500)
);


--
-- Name: vocabulary_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.vocabulary_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: vocabulary_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.vocabulary_items_id_seq OWNED BY public.vocabulary_items.id;


--
-- Name: calibration_questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_questions ALTER COLUMN id SET DEFAULT nextval('public.calibration_questions_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: levels id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.levels ALTER COLUMN id SET DEFAULT nextval('public.levels_id_seq'::regclass);


--
-- Name: missions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missions ALTER COLUMN id SET DEFAULT nextval('public.missions_id_seq'::regclass);


--
-- Name: question_options id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_options ALTER COLUMN id SET DEFAULT nextval('public.question_options_id_seq'::regclass);


--
-- Name: questions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions ALTER COLUMN id SET DEFAULT nextval('public.questions_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: user_mission_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_mission_progress ALTER COLUMN id SET DEFAULT nextval('public.user_mission_progress_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vocabulary_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vocabulary_items ALTER COLUMN id SET DEFAULT nextval('public.vocabulary_items_id_seq'::regclass);


--
-- Data for Name: calibration_questions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.calibration_questions (id, question_text, cefr_level, option_a, option_b, option_c, option_d, correct_option) FROM stdin;
1	She ___ from Spain.	A1	am	is	are	be	B
2	There ___ two cats on the sofa.	A1	is	are	be	was	B
3	I ___ coffee every morning.	A1	drink	drinks	drinking	drank	A
4	This is my sister. ___ name is Emma.	A1	His	Her	Its	Their	B
5	We ___ to the beach last weekend.	A2	go	went	gone	going	B
6	This exam is ___ than the last one.	A2	difficult	more difficult	most difficult	difficulty	B
7	I've lived here ___ three years.	A2	since	for	from	during	B
8	You ___ smoke here. It's forbidden.	A2	mustn't	don't have to	needn't	shouldn't have	A
9	By the time we arrived, the film ___ already ___.	B1	has / started	had / started	was / starting	have / started	B
10	She's the woman ___ car was stolen.	B1	who	which	whose	whom	C
11	I wish I ___ more time to study.	B1	have	had	will have	would have	B
12	He suggested ___ the meeting until Friday.	B1	to postpone	postponing	postpone	postponed	B
13	Hardly ___ the office when it started raining.	B2	I had left	had I left	I left	did I leave	B
14	If she ___ harder, she would have passed.	B2	studied	had studied	studies	would study	B
15	I'd rather you ___ tell anyone about this.	B2	don't	didn't	haven't	won't	B
16	The manager made us ___ the report twice.	B2	to rewrite	rewriting	rewrite	rewrote	C
17	___ had she finished speaking than the audience erupted.	C1	No sooner	Hardly	Scarcely	Only when	A
18	The evidence is far from ___ conclusive.	C1	being	be	been	to be	A
19	It was such a compelling argument that few could ___ it.	C1	refute	refuse	refund	refuel	A
20	He tends to ___ the point rather than answer directly.	C1	evade	invade	pervade	cascade	A
21	Were it not ___ your help, we would have failed.	C1	for	of	to	with	A
22	His remarks were so ___ that no one could pin down his real position.	C2	equivocal	equitable	equivalent	unequivocal	A
23	The report was criticised for being ___ and full of contradictions.	C2	incoherent	cohesive	concise	consistent	A
24	She has an ___ capacity for remembering names and faces.	C2	uncanny	uncaring	uncouth	uncommon	A
25	The two theories, though different, are not mutually ___.	C2	exclusive	exclusionary	excluded	excluding	A
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.groups (id, name, created_at) FROM stdin;
\.


--
-- Data for Name: levels; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.levels (id, code, title) FROM stdin;
1	A1	Beginner
2	A2	Elementary
3	B1	Intermediate
4	B2	Upper Intermediate
5	C1	Advanced
6	C2	Proficiency
\.


--
-- Data for Name: missions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.missions (id, level_id, order_index, title, description, is_active) FROM stdin;
1	1	1	A1 Mission 1	Beginner lesson number 1	t
2	1	2	A1 Mission 2	Beginner lesson number 2	t
3	1	3	A1 Mission 3	Beginner lesson number 3	t
4	1	4	A1 Mission 4	Beginner lesson number 4	t
5	1	5	A1 Mission 5	Beginner lesson number 5	t
6	2	1	qwerty	qwertyui	t
\.


--
-- Data for Name: question_options; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.question_options (id, question_id, option_text, translation_ru, is_correct, image_url) FROM stdin;
1	1	apple	яблоко	t	https://placehold.co/160x160?text=apple
2	1	book	книга	f	https://placehold.co/160x160?text=book
3	1	car	машина	f	https://placehold.co/160x160?text=car
4	1	water	вода	f	https://placehold.co/160x160?text=water
5	2	house	дом	f	https://placehold.co/160x160?text=house
6	2	book	книга	t	https://placehold.co/160x160?text=book
7	2	apple	яблоко	f	https://placehold.co/160x160?text=apple
8	2	water	вода	f	https://placehold.co/160x160?text=water
9	3	apple	яблоко	f	https://placehold.co/160x160?text=apple
10	3	water	вода	f	https://placehold.co/160x160?text=water
11	3	car	машина	t	https://placehold.co/160x160?text=car
12	3	book	книга	f	https://placehold.co/160x160?text=book
13	4	house	дом	t	https://placehold.co/160x160?text=house
14	4	car	машина	f	https://placehold.co/160x160?text=car
15	4	book	книга	f	https://placehold.co/160x160?text=book
16	4	apple	яблоко	f	https://placehold.co/160x160?text=apple
17	5	water	вода	t	https://placehold.co/160x160?text=water
18	5	apple	яблоко	f	https://placehold.co/160x160?text=apple
19	5	house	дом	f	https://placehold.co/160x160?text=house
20	5	car	машина	f	https://placehold.co/160x160?text=car
21	6	apple	яблоко	t	https://placehold.co/160x160?text=apple
22	7	book	книга	t	https://placehold.co/160x160?text=book
23	8	car	машина	t	https://placehold.co/160x160?text=car
24	9	house	дом	t	https://placehold.co/160x160?text=house
25	10	water	вода	t	https://placehold.co/160x160?text=water
26	11	apple	яблоко	t	https://placehold.co/160x160?text=apple
27	11	book	книга	f	https://placehold.co/160x160?text=book
28	11	car	машина	f	https://placehold.co/160x160?text=car
29	11	water	вода	f	https://placehold.co/160x160?text=water
30	12	house	дом	f	https://placehold.co/160x160?text=house
31	12	book	книга	t	https://placehold.co/160x160?text=book
32	12	apple	яблоко	f	https://placehold.co/160x160?text=apple
33	12	water	вода	f	https://placehold.co/160x160?text=water
34	13	apple	яблоко	f	https://placehold.co/160x160?text=apple
35	13	water	вода	f	https://placehold.co/160x160?text=water
36	13	car	машина	t	https://placehold.co/160x160?text=car
37	13	book	книга	f	https://placehold.co/160x160?text=book
38	14	house	дом	t	https://placehold.co/160x160?text=house
39	14	car	машина	f	https://placehold.co/160x160?text=car
40	14	book	книга	f	https://placehold.co/160x160?text=book
41	14	apple	яблоко	f	https://placehold.co/160x160?text=apple
42	15	water	вода	t	https://placehold.co/160x160?text=water
43	15	apple	яблоко	f	https://placehold.co/160x160?text=apple
44	15	house	дом	f	https://placehold.co/160x160?text=house
45	15	car	машина	f	https://placehold.co/160x160?text=car
46	16	apple	яблоко	t	https://placehold.co/160x160?text=apple
47	17	book	книга	t	https://placehold.co/160x160?text=book
48	18	car	машина	t	https://placehold.co/160x160?text=car
49	19	house	дом	t	https://placehold.co/160x160?text=house
50	20	water	вода	t	https://placehold.co/160x160?text=water
51	21	apple	яблоко	t	https://placehold.co/160x160?text=apple
52	21	book	книга	f	https://placehold.co/160x160?text=book
53	21	car	машина	f	https://placehold.co/160x160?text=car
54	21	water	вода	f	https://placehold.co/160x160?text=water
55	22	house	дом	f	https://placehold.co/160x160?text=house
56	22	book	книга	t	https://placehold.co/160x160?text=book
57	22	apple	яблоко	f	https://placehold.co/160x160?text=apple
58	22	water	вода	f	https://placehold.co/160x160?text=water
59	23	apple	яблоко	f	https://placehold.co/160x160?text=apple
60	23	water	вода	f	https://placehold.co/160x160?text=water
61	23	car	машина	t	https://placehold.co/160x160?text=car
62	23	book	книга	f	https://placehold.co/160x160?text=book
63	24	house	дом	t	https://placehold.co/160x160?text=house
64	24	car	машина	f	https://placehold.co/160x160?text=car
65	24	book	книга	f	https://placehold.co/160x160?text=book
66	24	apple	яблоко	f	https://placehold.co/160x160?text=apple
67	25	water	вода	t	https://placehold.co/160x160?text=water
68	25	apple	яблоко	f	https://placehold.co/160x160?text=apple
69	25	house	дом	f	https://placehold.co/160x160?text=house
70	25	car	машина	f	https://placehold.co/160x160?text=car
71	26	apple	яблоко	t	https://placehold.co/160x160?text=apple
72	27	book	книга	t	https://placehold.co/160x160?text=book
73	28	car	машина	t	https://placehold.co/160x160?text=car
74	29	house	дом	t	https://placehold.co/160x160?text=house
75	30	water	вода	t	https://placehold.co/160x160?text=water
76	31	apple	яблоко	t	https://placehold.co/160x160?text=apple
77	31	book	книга	f	https://placehold.co/160x160?text=book
78	31	car	машина	f	https://placehold.co/160x160?text=car
79	31	water	вода	f	https://placehold.co/160x160?text=water
80	32	house	дом	f	https://placehold.co/160x160?text=house
81	32	book	книга	t	https://placehold.co/160x160?text=book
82	32	apple	яблоко	f	https://placehold.co/160x160?text=apple
83	32	water	вода	f	https://placehold.co/160x160?text=water
84	33	apple	яблоко	f	https://placehold.co/160x160?text=apple
85	33	water	вода	f	https://placehold.co/160x160?text=water
86	33	car	машина	t	https://placehold.co/160x160?text=car
87	33	book	книга	f	https://placehold.co/160x160?text=book
88	34	house	дом	t	https://placehold.co/160x160?text=house
89	34	car	машина	f	https://placehold.co/160x160?text=car
90	34	book	книга	f	https://placehold.co/160x160?text=book
91	34	apple	яблоко	f	https://placehold.co/160x160?text=apple
92	35	water	вода	t	https://placehold.co/160x160?text=water
93	35	apple	яблоко	f	https://placehold.co/160x160?text=apple
94	35	house	дом	f	https://placehold.co/160x160?text=house
95	35	car	машина	f	https://placehold.co/160x160?text=car
96	36	apple	яблоко	t	https://placehold.co/160x160?text=apple
97	37	book	книга	t	https://placehold.co/160x160?text=book
98	38	car	машина	t	https://placehold.co/160x160?text=car
99	39	house	дом	t	https://placehold.co/160x160?text=house
100	40	water	вода	t	https://placehold.co/160x160?text=water
101	41	apple	яблоко	t	https://placehold.co/160x160?text=apple
102	41	book	книга	f	https://placehold.co/160x160?text=book
103	41	car	машина	f	https://placehold.co/160x160?text=car
104	41	water	вода	f	https://placehold.co/160x160?text=water
105	42	house	дом	f	https://placehold.co/160x160?text=house
106	42	book	книга	t	https://placehold.co/160x160?text=book
107	42	apple	яблоко	f	https://placehold.co/160x160?text=apple
108	42	water	вода	f	https://placehold.co/160x160?text=water
109	43	apple	яблоко	f	https://placehold.co/160x160?text=apple
110	43	water	вода	f	https://placehold.co/160x160?text=water
111	43	car	машина	t	https://placehold.co/160x160?text=car
112	43	book	книга	f	https://placehold.co/160x160?text=book
113	44	house	дом	t	https://placehold.co/160x160?text=house
114	44	car	машина	f	https://placehold.co/160x160?text=car
115	44	book	книга	f	https://placehold.co/160x160?text=book
116	44	apple	яблоко	f	https://placehold.co/160x160?text=apple
117	45	water	вода	t	https://placehold.co/160x160?text=water
118	45	apple	яблоко	f	https://placehold.co/160x160?text=apple
119	45	house	дом	f	https://placehold.co/160x160?text=house
120	45	car	машина	f	https://placehold.co/160x160?text=car
121	46	apple	яблоко	t	https://placehold.co/160x160?text=apple
122	47	book	книга	t	https://placehold.co/160x160?text=book
123	48	car	машина	t	https://placehold.co/160x160?text=car
124	49	house	дом	t	https://placehold.co/160x160?text=house
125	50	water	вода	t	https://placehold.co/160x160?text=water
130	53	nigger	\N	t	\N
131	53	white man	\N	f	\N
128	52	nigger	харощий чилавек	t	https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9JytHFGa9a4Usgw59zkz1EgQUxS-uvEP7OKb7uhjMiLFbfwRz2HTY7zg&s=10
129	52	white man	да	f	https://static0.srcdn.com/wordpress/wp-content/uploads/2020/02/Breaking-Bad-things-Walter-White-feature.jpg?w=1600&h=900&fit=crop
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.questions (id, task_id, question_text, question_type) FROM stdin;
1	1	Which word means «яблоко»?	multiple_choice
2	1	Which word means «книга»?	multiple_choice
3	1	Which word means «машина»?	multiple_choice
4	1	Which word means «дом»?	multiple_choice
5	1	Which word means «вода»?	multiple_choice
6	2	Say the English word for «яблоко»	translation
7	2	Say the English word for «книга»	translation
8	2	Say the English word for «машина»	translation
9	2	Say the English word for «дом»	translation
10	2	Say the English word for «вода»	translation
11	4	Which word means «яблоко»?	multiple_choice
12	4	Which word means «книга»?	multiple_choice
13	4	Which word means «машина»?	multiple_choice
14	4	Which word means «дом»?	multiple_choice
15	4	Which word means «вода»?	multiple_choice
16	5	Say the English word for «яблоко»	translation
17	5	Say the English word for «книга»	translation
18	5	Say the English word for «машина»	translation
19	5	Say the English word for «дом»	translation
20	5	Say the English word for «вода»	translation
21	7	Which word means «яблоко»?	multiple_choice
22	7	Which word means «книга»?	multiple_choice
23	7	Which word means «машина»?	multiple_choice
24	7	Which word means «дом»?	multiple_choice
25	7	Which word means «вода»?	multiple_choice
26	8	Say the English word for «яблоко»	translation
27	8	Say the English word for «книга»	translation
28	8	Say the English word for «машина»	translation
29	8	Say the English word for «дом»	translation
30	8	Say the English word for «вода»	translation
31	10	Which word means «яблоко»?	multiple_choice
32	10	Which word means «книга»?	multiple_choice
33	10	Which word means «машина»?	multiple_choice
34	10	Which word means «дом»?	multiple_choice
35	10	Which word means «вода»?	multiple_choice
36	11	Say the English word for «яблоко»	translation
37	11	Say the English word for «книга»	translation
38	11	Say the English word for «машина»	translation
39	11	Say the English word for «дом»	translation
40	11	Say the English word for «вода»	translation
41	13	Which word means «яблоко»?	multiple_choice
42	13	Which word means «книга»?	multiple_choice
43	13	Which word means «машина»?	multiple_choice
44	13	Which word means «дом»?	multiple_choice
45	13	Which word means «вода»?	multiple_choice
46	14	Say the English word for «яблоко»	translation
47	14	Say the English word for «книга»	translation
48	14	Say the English word for «машина»	translation
49	14	Say the English word for «дом»	translation
50	14	Say the English word for «вода»	translation
52	16	Джарахмула	multiple_choice
53	18	харощий чилавек	multiple_choice
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, name) FROM stdin;
1	student
2	teacher
5	student_jarahmalla
7	student_q
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tasks (id, mission_id, title, description, task_type, order_number, time_limit, xp_reward_first, xp_reward_repeat) FROM stdin;
1	1	Test	\N	multiple_choice	1	\N	100	10
2	1	Pronunciation	\N	translation	2	\N	150	15
3	1	Dictionary game	\N	vocabulary_game	3	\N	120	12
4	2	Test	\N	multiple_choice	1	\N	100	10
5	2	Pronunciation	\N	translation	2	\N	150	15
6	2	Dictionary game	\N	vocabulary_game	3	\N	120	12
7	3	Test	\N	multiple_choice	1	\N	100	10
8	3	Pronunciation	\N	translation	2	\N	150	15
9	3	Dictionary game	\N	vocabulary_game	3	\N	120	12
10	4	Test	\N	multiple_choice	1	\N	100	10
11	4	Pronunciation	\N	translation	2	\N	150	15
12	4	Dictionary game	\N	vocabulary_game	3	\N	120	12
13	5	Test	\N	multiple_choice	1	\N	100	10
14	5	Pronunciation	\N	translation	2	\N	150	15
15	5	Dictionary game	\N	vocabulary_game	3	\N	120	12
16	6	Vocabulary	\N	multiple_choice	1	\N	100	10
18	6	йцукуу	\N	vocabulary_game	1	\N	100	10
\.


--
-- Data for Name: user_mission_progress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_mission_progress (id, user_id, mission_id, is_completed, tests_passed, pronunciation_passed, best_score_percentage, completion_count, last_completed_at) FROM stdin;
1	2	1	t	t	t	100	1	2026-10-02 15:21:24.299177
2	1	6	f	t	f	0	0	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, first_name, last_name, email, password_hash, cefr_level, level_id, total_xp, is_calibrated, role_id, group_id, created_at, updated_at) FROM stdin;
1	Teacher	Quest	teacher@englishquest.dev	$2b$12$tfQNVWhMk6Wocwv.4n4BEuTFoTGXToCtrvHYOz/.5usZ5s.MVX1lO	C2	6	0	t	2	\N	2026-10-02 10:59:30.616828	2026-10-02 10:59:30.616828
2	l	l	l@l.l	$2b$12$mpX15K3lD5VK6wDUXie0VOFLVcS010D2oQ/dVYhISO/pjKAzmhZv6	A1	1	370	t	1	\N	2026-10-02 11:05:13.482309	2026-10-02 20:21:24.265043
\.


--
-- Data for Name: vocabulary_items; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.vocabulary_items (id, level_id, word_en, word_ru, transcription, image_url) FROM stdin;
1	1	apple	яблоко	/ˈæp.əl/	/images/apple.svg
2	1	book	книга	/bʊk/	/images/book.svg
3	1	car	машина	/kɑːr/	/images/car.svg
4	1	house	дом	/haʊs/	/images/house.svg
5	1	water	вода	/ˈwɔː.tər/	/images/water.svg
6	1	dog	собака	/dɒɡ/	/images/dog.svg
7	1	cat	кошка	/kæt/	/images/cat.svg
8	1	sun	солнце	/sʌn/	/images/sun.svg
9	1	milk	молоко	/mɪlk/	/images/milk.svg
10	1	bread	хлеб	/bred/	/images/bread.svg
11	1	fish	рыба	/fɪʃ/	/images/fish.svg
12	1	tree	дерево	/triː/	/images/tree.svg
13	1	bird	птица	/bɜːd/	/images/bird.svg
14	1	door	дверь	/dɔːr/	/images/door.svg
15	1	ball	мяч	/bɔːl/	/images/ball.svg
16	2	weather	погода	/ˈweð.ər/	\N
17	2	holiday	отпуск	/ˈhɒl.ə.deɪ/	\N
18	2	market	рынок	/ˈmɑː.kɪt/	\N
19	2	letter	письмо	/ˈlet.ər/	\N
20	2	window	окно	/ˈwɪn.dəʊ/	\N
21	2	bridge	мост	/brɪdʒ/	\N
22	2	forest	лес	/ˈfɒr.ɪst/	\N
23	2	river	река	/ˈrɪv.ər/	\N
24	2	village	деревня	/ˈvɪl.ɪdʒ/	\N
25	2	island	остров	/ˈaɪ.lənd/	\N
26	3	decision	решение	/dɪˈsɪʒ.ən/	\N
27	3	knowledge	знание	/ˈnɒl.ɪdʒ/	\N
28	3	research	исследование	/rɪˈsɜːtʃ/	\N
29	3	advantage	преимущество	/ədˈvɑːn.tɪdʒ/	\N
30	3	opinion	мнение	/əˈpɪn.jən/	\N
31	3	purpose	цель	/ˈpɜː.pəs/	\N
32	3	effort	усилие	/ˈef.ət/	\N
33	3	environment	окружающая среда	/ɪnˈvaɪ.rən.mənt/	\N
34	3	experience	опыт	/ɪkˈspɪə.ri.əns/	\N
35	3	opportunity	возможность	/ˌɒp.əˈtjuː.nə.ti/	\N
36	4	approach	подход	/əˈprəʊtʃ/	\N
37	4	consequence	последствие	/ˈkɒn.sɪ.kwəns/	\N
38	4	estimate	оценка	/ˈes.tɪ.meɪt/	\N
39	4	evidence	доказательство	/ˈev.ɪ.dəns/	\N
40	4	impact	влияние	/ˈɪm.pækt/	\N
41	4	issue	проблема	/ˈɪʃ.uː/	\N
42	4	maintain	поддерживать	/meɪnˈteɪn/	\N
43	4	obtain	получать	/əbˈteɪn/	\N
44	4	relevant	соответствующий	/ˈrel.ə.vənt/	\N
45	4	significant	значительный	/sɪɡˈnɪf.ɪ.kənt/	\N
46	5	ambiguous	двусмысленный	/æmˈbɪɡ.ju.əs/	\N
47	5	coherent	связный	/kəʊˈhɪə.rənt/	\N
48	5	comprehensive	всеобъемлющий	/ˌkɒm.prɪˈhen.sɪv/	\N
49	5	inevitable	неизбежный	/ɪnˈev.ɪ.tə.bəl/	\N
50	5	perceive	воспринимать	/pəˈsiːv/	\N
51	5	profound	глубокий	/prəˈfaʊnd/	\N
52	5	reluctant	неохотный	/rɪˈlʌk.tənt/	\N
53	5	subtle	тонкий	/ˈsʌt.əl/	\N
54	5	sustain	поддерживать	/səˈsteɪn/	\N
55	5	versatile	универсальный	/ˈvɜː.sə.taɪl/	\N
56	6	ephemeral	мимолётный	/ɪˈfem.ər.əl/	\N
57	6	idiosyncratic	своеобразный	/ˌɪd.i.ə.sɪŋˈkræt.ɪk/	\N
58	6	ubiquitous	вездесущий	/juːˈbɪk.wɪ.təs/	\N
59	6	quintessential	типичный	/ˌkwɪn.tɪˈsen.ʃəl/	\N
60	6	pragmatic	прагматичный	/præɡˈmæt.ɪk/	\N
61	6	nuance	нюанс	/ˈnjuː.ɑːns/	\N
62	6	cohesive	сплочённый	/kəʊˈhiː.sɪv/	\N
63	6	formidable	внушительный	/fɔːˈmɪd.ə.bəl/	\N
64	6	lucid	ясный	/ˈluː.sɪd/	\N
65	6	scrutinize	тщательно изучать	/ˈskruː.tɪ.naɪz/	\N
67	1	Qwerty	йцукен	\N	\N
68	1	nigger	харощий чилавек	\N	https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9JytHFGa9a4Usgw59zkz1EgQUxS-uvEP7OKb7uhjMiLFbfwRz2HTY7zg&s=10
69	1	white man	да	\N	https://static0.srcdn.com/wordpress/wp-content/uploads/2020/02/Breaking-Bad-things-Walter-White-feature.jpg?w=1600&h=900&fit=crop
\.


--
-- Name: calibration_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.calibration_questions_id_seq', 27, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.groups_id_seq', 1, false);


--
-- Name: levels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.levels_id_seq', 23, true);


--
-- Name: missions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.missions_id_seq', 42, true);


--
-- Name: question_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.question_options_id_seq', 131, true);


--
-- Name: questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.questions_id_seq', 53, true);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.roles_id_seq', 44, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tasks_id_seq', 36, true);


--
-- Name: user_mission_progress_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_mission_progress_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 27, true);


--
-- Name: vocabulary_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.vocabulary_items_id_seq', 69, true);


--
-- Name: calibration_questions calibration_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_questions
    ADD CONSTRAINT calibration_questions_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: levels levels_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.levels
    ADD CONSTRAINT levels_code_key UNIQUE (code);


--
-- Name: levels levels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.levels
    ADD CONSTRAINT levels_pkey PRIMARY KEY (id);


--
-- Name: missions missions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missions
    ADD CONSTRAINT missions_pkey PRIMARY KEY (id);


--
-- Name: question_options question_options_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: missions uq_missions_level_order; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missions
    ADD CONSTRAINT uq_missions_level_order UNIQUE (level_id, order_index);


--
-- Name: user_mission_progress uq_progress_user_mission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_mission_progress
    ADD CONSTRAINT uq_progress_user_mission UNIQUE (user_id, mission_id);


--
-- Name: user_mission_progress user_mission_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_mission_progress
    ADD CONSTRAINT user_mission_progress_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vocabulary_items vocabulary_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vocabulary_items
    ADD CONSTRAINT vocabulary_items_pkey PRIMARY KEY (id);


--
-- Name: missions missions_level_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.missions
    ADD CONSTRAINT missions_level_id_fkey FOREIGN KEY (level_id) REFERENCES public.levels(id);


--
-- Name: question_options question_options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.question_options
    ADD CONSTRAINT question_options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- Name: questions questions_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: tasks tasks_mission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_mission_id_fkey FOREIGN KEY (mission_id) REFERENCES public.missions(id) ON DELETE CASCADE;


--
-- Name: user_mission_progress user_mission_progress_mission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_mission_progress
    ADD CONSTRAINT user_mission_progress_mission_id_fkey FOREIGN KEY (mission_id) REFERENCES public.missions(id);


--
-- Name: user_mission_progress user_mission_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_mission_progress
    ADD CONSTRAINT user_mission_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users users_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: users users_level_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_level_id_fkey FOREIGN KEY (level_id) REFERENCES public.levels(id);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: vocabulary_items vocabulary_items_level_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vocabulary_items
    ADD CONSTRAINT vocabulary_items_level_id_fkey FOREIGN KEY (level_id) REFERENCES public.levels(id);


--
-- PostgreSQL database dump complete
--

\unrestrict qfqwGClDi31roJyuswaqzohKBDO6PZI9XQDJ2THlpXgCr2n6j19HeeCm9EZ0x7y

