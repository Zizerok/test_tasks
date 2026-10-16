--
-- PostgreSQL database dump
--

\restrict eLU81QXU93Yw6jtchGctVS5JObl7OylGOo9XuihWPOGBtY0amNzGbbWc3ghtbHI

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

-- Started on 2026-10-15 18:43:07

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 250 (class 1259 OID 16592)
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.activity_logs (
    id integer NOT NULL,
    business_id integer NOT NULL,
    action_type text NOT NULL,
    entity_type text NOT NULL,
    entity_id integer,
    related_employee_id integer,
    related_shift_id integer,
    description text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.activity_logs OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 16591)
-- Name: activity_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.activity_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.activity_logs_id_seq OWNER TO postgres;

--
-- TOC entry 5115 (class 0 OID 0)
-- Dependencies: 249
-- Name: activity_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.activity_logs_id_seq OWNED BY public.activity_logs.id;


--
-- TOC entry 222 (class 1259 OID 16403)
-- Name: businesses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.businesses (
    id integer NOT NULL,
    owner_id integer,
    name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.businesses OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16402)
-- Name: businesses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.businesses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.businesses_id_seq OWNER TO postgres;

--
-- TOC entry 5116 (class 0 OID 0)
-- Dependencies: 221
-- Name: businesses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.businesses_id_seq OWNED BY public.businesses.id;


--
-- TOC entry 224 (class 1259 OID 16414)
-- Name: employees; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    business_id integer NOT NULL,
    full_name text NOT NULL,
    last_name text,
    first_name text,
    middle_name text,
    birth_date text,
    gender text,
    phone text,
    vk_id text,
    "position" text,
    is_active integer DEFAULT 1,
    hired_date text,
    comment text,
    salary_rate text,
    photo_path text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.employees OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16413)
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employees_id_seq OWNER TO postgres;

--
-- TOC entry 5117 (class 0 OID 0)
-- Dependencies: 223
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- TOC entry 236 (class 1259 OID 16495)
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    business_id integer NOT NULL,
    shift_id integer,
    recipient_type text,
    recipient_label text,
    notification_type text,
    message_text text,
    channel text DEFAULT 'VK'::text,
    send_status text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 16494)
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- TOC entry 5118 (class 0 OID 0)
-- Dependencies: 235
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- TOC entry 228 (class 1259 OID 16441)
-- Name: position_capabilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.position_capabilities (
    id integer NOT NULL,
    position_id integer NOT NULL,
    covered_position_id integer NOT NULL,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.position_capabilities OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16440)
-- Name: position_capabilities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.position_capabilities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.position_capabilities_id_seq OWNER TO postgres;

--
-- TOC entry 5119 (class 0 OID 0)
-- Dependencies: 227
-- Name: position_capabilities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.position_capabilities_id_seq OWNED BY public.position_capabilities.id;


--
-- TOC entry 226 (class 1259 OID 16428)
-- Name: positions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.positions (
    id integer NOT NULL,
    business_id integer NOT NULL,
    name text NOT NULL,
    salary real,
    base_position_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.positions OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16427)
-- Name: positions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.positions_id_seq OWNER TO postgres;

--
-- TOC entry 5120 (class 0 OID 0)
-- Dependencies: 225
-- Name: positions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.positions_id_seq OWNED BY public.positions.id;


--
-- TOC entry 242 (class 1259 OID 16536)
-- Name: sent_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sent_notifications (
    id integer NOT NULL,
    shift_id integer,
    user_id integer,
    message_text text,
    send_status text NOT NULL,
    error_text text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.sent_notifications OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 16535)
-- Name: sent_notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sent_notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sent_notifications_id_seq OWNER TO postgres;

--
-- TOC entry 5121 (class 0 OID 0)
-- Dependencies: 241
-- Name: sent_notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sent_notifications_id_seq OWNED BY public.sent_notifications.id;


--
-- TOC entry 232 (class 1259 OID 16467)
-- Name: shift_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_assignments (
    id integer NOT NULL,
    shift_id integer NOT NULL,
    employee_id integer NOT NULL,
    position_name text NOT NULL,
    payment_type text NOT NULL,
    hourly_rate text,
    fixed_rate text,
    percent_rate text,
    revenue_amount text,
    is_paid integer DEFAULT 0,
    paid_at text,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_assignments OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16466)
-- Name: shift_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_assignments_id_seq OWNER TO postgres;

--
-- TOC entry 5122 (class 0 OID 0)
-- Dependencies: 231
-- Name: shift_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_assignments_id_seq OWNED BY public.shift_assignments.id;


--
-- TOC entry 234 (class 1259 OID 16481)
-- Name: shift_open_positions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_open_positions (
    id integer NOT NULL,
    shift_id integer NOT NULL,
    position_name text NOT NULL,
    employee_count integer NOT NULL,
    payment_type text NOT NULL,
    hourly_rate text,
    fixed_rate text,
    percent_rate text,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_open_positions OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16480)
-- Name: shift_open_positions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_open_positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_open_positions_id_seq OWNER TO postgres;

--
-- TOC entry 5123 (class 0 OID 0)
-- Dependencies: 233
-- Name: shift_open_positions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_open_positions_id_seq OWNED BY public.shift_open_positions.id;


--
-- TOC entry 238 (class 1259 OID 16508)
-- Name: shift_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_responses (
    id integer NOT NULL,
    business_id integer NOT NULL,
    shift_id integer,
    vk_id text,
    employee_id integer,
    position_name text,
    response_status text,
    response_message text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed_at text,
    raw_payload text,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_responses OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 16507)
-- Name: shift_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_responses_id_seq OWNER TO postgres;

--
-- TOC entry 5124 (class 0 OID 0)
-- Dependencies: 237
-- Name: shift_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_responses_id_seq OWNED BY public.shift_responses.id;


--
-- TOC entry 246 (class 1259 OID 16564)
-- Name: shift_template_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_template_assignments (
    id integer NOT NULL,
    template_id integer NOT NULL,
    employee_id integer NOT NULL,
    position_name text NOT NULL,
    payment_type text NOT NULL,
    hourly_rate text,
    fixed_rate text,
    percent_rate text,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_template_assignments OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 16563)
-- Name: shift_template_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_template_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_template_assignments_id_seq OWNER TO postgres;

--
-- TOC entry 5125 (class 0 OID 0)
-- Dependencies: 245
-- Name: shift_template_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_template_assignments_id_seq OWNED BY public.shift_template_assignments.id;


--
-- TOC entry 248 (class 1259 OID 16578)
-- Name: shift_template_open_positions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_template_open_positions (
    id integer NOT NULL,
    template_id integer NOT NULL,
    position_name text NOT NULL,
    employee_count integer NOT NULL,
    payment_type text NOT NULL,
    hourly_rate text,
    fixed_rate text,
    percent_rate text,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_template_open_positions OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 16577)
-- Name: shift_template_open_positions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_template_open_positions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_template_open_positions_id_seq OWNER TO postgres;

--
-- TOC entry 5126 (class 0 OID 0)
-- Dependencies: 247
-- Name: shift_template_open_positions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_template_open_positions_id_seq OWNED BY public.shift_template_open_positions.id;


--
-- TOC entry 244 (class 1259 OID 16548)
-- Name: shift_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shift_templates (
    id integer NOT NULL,
    business_id integer NOT NULL,
    name text NOT NULL,
    start_time text NOT NULL,
    end_time text NOT NULL,
    status text NOT NULL,
    comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shift_templates OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 16547)
-- Name: shift_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shift_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shift_templates_id_seq OWNER TO postgres;

--
-- TOC entry 5127 (class 0 OID 0)
-- Dependencies: 243
-- Name: shift_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shift_templates_id_seq OWNED BY public.shift_templates.id;


--
-- TOC entry 230 (class 1259 OID 16451)
-- Name: shifts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.shifts (
    id integer NOT NULL,
    business_id integer NOT NULL,
    shift_date text NOT NULL,
    start_time text NOT NULL,
    end_time text NOT NULL,
    status text NOT NULL,
    comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.shifts OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16450)
-- Name: shifts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.shifts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shifts_id_seq OWNER TO postgres;

--
-- TOC entry 5128 (class 0 OID 0)
-- Dependencies: 229
-- Name: shifts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.shifts_id_seq OWNED BY public.shifts.id;


--
-- TOC entry 254 (class 1259 OID 16626)
-- Name: sync_conflicts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sync_conflicts (
    id integer NOT NULL,
    business_id integer,
    entity_type text NOT NULL,
    entity_id integer,
    conflict_type text NOT NULL,
    server_payload_json jsonb,
    local_payload_json jsonb,
    server_version integer,
    local_version integer,
    resolution_status text DEFAULT 'unresolved'::text,
    resolution_comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp without time zone
);


ALTER TABLE public.sync_conflicts OWNER TO postgres;

--
-- TOC entry 253 (class 1259 OID 16625)
-- Name: sync_conflicts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sync_conflicts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_conflicts_id_seq OWNER TO postgres;

--
-- TOC entry 5129 (class 0 OID 0)
-- Dependencies: 253
-- Name: sync_conflicts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sync_conflicts_id_seq OWNED BY public.sync_conflicts.id;


--
-- TOC entry 252 (class 1259 OID 16607)
-- Name: sync_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sync_queue (
    id integer NOT NULL,
    operation_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    business_id integer,
    entity_type text NOT NULL,
    entity_id integer,
    operation_type text NOT NULL,
    payload_json jsonb,
    base_version integer DEFAULT 1,
    local_version integer DEFAULT 1,
    status text DEFAULT 'pending'::text,
    error_text text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    synced_at timestamp without time zone
);


ALTER TABLE public.sync_queue OWNER TO postgres;

--
-- TOC entry 251 (class 1259 OID 16606)
-- Name: sync_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sync_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_queue_id_seq OWNER TO postgres;

--
-- TOC entry 5130 (class 0 OID 0)
-- Dependencies: 251
-- Name: sync_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sync_queue_id_seq OWNED BY public.sync_queue.id;


--
-- TOC entry 220 (class 1259 OID 16390)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    login text,
    email text,
    password_hash text,
    salt text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16389)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 5131 (class 0 OID 0)
-- Dependencies: 219
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 240 (class 1259 OID 16520)
-- Name: vk_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vk_settings (
    id integer NOT NULL,
    business_id integer NOT NULL,
    group_id text,
    community_token text,
    backend_url text,
    is_enabled integer DEFAULT 0,
    sync_uuid text DEFAULT md5(((random())::text || (clock_timestamp())::text)),
    sync_version integer DEFAULT 1,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deleted_at timestamp without time zone
);


ALTER TABLE public.vk_settings OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 16519)
-- Name: vk_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vk_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vk_settings_id_seq OWNER TO postgres;

--
-- TOC entry 5132 (class 0 OID 0)
-- Dependencies: 239
-- Name: vk_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vk_settings_id_seq OWNED BY public.vk_settings.id;


--
-- TOC entry 4910 (class 2604 OID 16595)
-- Name: activity_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs ALTER COLUMN id SET DEFAULT nextval('public.activity_logs_id_seq'::regclass);


--
-- TOC entry 4845 (class 2604 OID 16406)
-- Name: businesses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses ALTER COLUMN id SET DEFAULT nextval('public.businesses_id_seq'::regclass);


--
-- TOC entry 4850 (class 2604 OID 16417)
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- TOC entry 4879 (class 2604 OID 16498)
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- TOC entry 4861 (class 2604 OID 16444)
-- Name: position_capabilities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.position_capabilities ALTER COLUMN id SET DEFAULT nextval('public.position_capabilities_id_seq'::regclass);


--
-- TOC entry 4856 (class 2604 OID 16431)
-- Name: positions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.positions ALTER COLUMN id SET DEFAULT nextval('public.positions_id_seq'::regclass);


--
-- TOC entry 4895 (class 2604 OID 16539)
-- Name: sent_notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sent_notifications ALTER COLUMN id SET DEFAULT nextval('public.sent_notifications_id_seq'::regclass);


--
-- TOC entry 4870 (class 2604 OID 16470)
-- Name: shift_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_assignments ALTER COLUMN id SET DEFAULT nextval('public.shift_assignments_id_seq'::regclass);


--
-- TOC entry 4875 (class 2604 OID 16484)
-- Name: shift_open_positions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_open_positions ALTER COLUMN id SET DEFAULT nextval('public.shift_open_positions_id_seq'::regclass);


--
-- TOC entry 4885 (class 2604 OID 16511)
-- Name: shift_responses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_responses ALTER COLUMN id SET DEFAULT nextval('public.shift_responses_id_seq'::regclass);


--
-- TOC entry 4902 (class 2604 OID 16567)
-- Name: shift_template_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_template_assignments ALTER COLUMN id SET DEFAULT nextval('public.shift_template_assignments_id_seq'::regclass);


--
-- TOC entry 4906 (class 2604 OID 16581)
-- Name: shift_template_open_positions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_template_open_positions ALTER COLUMN id SET DEFAULT nextval('public.shift_template_open_positions_id_seq'::regclass);


--
-- TOC entry 4897 (class 2604 OID 16551)
-- Name: shift_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_templates ALTER COLUMN id SET DEFAULT nextval('public.shift_templates_id_seq'::regclass);


--
-- TOC entry 4865 (class 2604 OID 16454)
-- Name: shifts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shifts ALTER COLUMN id SET DEFAULT nextval('public.shifts_id_seq'::regclass);


--
-- TOC entry 4918 (class 2604 OID 16629)
-- Name: sync_conflicts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_conflicts ALTER COLUMN id SET DEFAULT nextval('public.sync_conflicts_id_seq'::regclass);


--
-- TOC entry 4912 (class 2604 OID 16610)
-- Name: sync_queue id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_queue ALTER COLUMN id SET DEFAULT nextval('public.sync_queue_id_seq'::regclass);


--
-- TOC entry 4840 (class 2604 OID 16393)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4890 (class 2604 OID 16523)
-- Name: vk_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_settings ALTER COLUMN id SET DEFAULT nextval('public.vk_settings_id_seq'::regclass);


--
-- TOC entry 4956 (class 2606 OID 16605)
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4926 (class 2606 OID 16412)
-- Name: businesses businesses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.businesses
    ADD CONSTRAINT businesses_pkey PRIMARY KEY (id);


--
-- TOC entry 4928 (class 2606 OID 16426)
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- TOC entry 4940 (class 2606 OID 16506)
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- TOC entry 4932 (class 2606 OID 16449)
-- Name: position_capabilities position_capabilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.position_capabilities
    ADD CONSTRAINT position_capabilities_pkey PRIMARY KEY (id);


--
-- TOC entry 4930 (class 2606 OID 16439)
-- Name: positions positions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.positions
    ADD CONSTRAINT positions_pkey PRIMARY KEY (id);


--
-- TOC entry 4948 (class 2606 OID 16546)
-- Name: sent_notifications sent_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sent_notifications
    ADD CONSTRAINT sent_notifications_pkey PRIMARY KEY (id);


--
-- TOC entry 4936 (class 2606 OID 16479)
-- Name: shift_assignments shift_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_assignments
    ADD CONSTRAINT shift_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 4938 (class 2606 OID 16493)
-- Name: shift_open_positions shift_open_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_open_positions
    ADD CONSTRAINT shift_open_positions_pkey PRIMARY KEY (id);


--
-- TOC entry 4942 (class 2606 OID 16518)
-- Name: shift_responses shift_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_responses
    ADD CONSTRAINT shift_responses_pkey PRIMARY KEY (id);


--
-- TOC entry 4952 (class 2606 OID 16576)
-- Name: shift_template_assignments shift_template_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_template_assignments
    ADD CONSTRAINT shift_template_assignments_pkey PRIMARY KEY (id);


--
-- TOC entry 4954 (class 2606 OID 16590)
-- Name: shift_template_open_positions shift_template_open_positions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_template_open_positions
    ADD CONSTRAINT shift_template_open_positions_pkey PRIMARY KEY (id);


--
-- TOC entry 4950 (class 2606 OID 16562)
-- Name: shift_templates shift_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shift_templates
    ADD CONSTRAINT shift_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 4934 (class 2606 OID 16465)
-- Name: shifts shifts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.shifts
    ADD CONSTRAINT shifts_pkey PRIMARY KEY (id);


--
-- TOC entry 4962 (class 2606 OID 16638)
-- Name: sync_conflicts sync_conflicts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_conflicts
    ADD CONSTRAINT sync_conflicts_pkey PRIMARY KEY (id);


--
-- TOC entry 4958 (class 2606 OID 16624)
-- Name: sync_queue sync_queue_operation_uuid_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_queue
    ADD CONSTRAINT sync_queue_operation_uuid_key UNIQUE (operation_uuid);


--
-- TOC entry 4960 (class 2606 OID 16622)
-- Name: sync_queue sync_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_queue
    ADD CONSTRAINT sync_queue_pkey PRIMARY KEY (id);


--
-- TOC entry 4922 (class 2606 OID 16401)
-- Name: users users_login_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_login_key UNIQUE (login);


--
-- TOC entry 4924 (class 2606 OID 16399)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4944 (class 2606 OID 16532)
-- Name: vk_settings vk_settings_business_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_settings
    ADD CONSTRAINT vk_settings_business_id_key UNIQUE (business_id);


--
-- TOC entry 4946 (class 2606 OID 16530)
-- Name: vk_settings vk_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vk_settings
    ADD CONSTRAINT vk_settings_pkey PRIMARY KEY (id);


-- Completed on 2026-10-15 18:43:08

--
-- PostgreSQL database dump complete
--

\unrestrict eLU81QXU93Yw6jtchGctVS5JObl7OylGOo9XuihWPOGBtY0amNzGbbWc3ghtbHI

