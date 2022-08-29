-- Copyright (C) 2022  E.SUN BANK.
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.

--  Name: answers; Type: TABLE; Schema: public;
--
CREATE TABLE  IF NOT EXISTS    public.answers (
    qid varchar,
    answer varchar,
    team_id integer,
    post_time timestamp without time zone DEFAULT now(),
    get_time numeric,
    status_code integer NOT NULL,
    retry integer,
    text json,
    s_uuid character varying,
    u_uuid character varying,
    seq_id serial,
    receive_time timestamp without time zone
);





--
-- Name: daily_task_status; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.daily_task_status (
    status integer
);

INSERT INTO public.daily_task_status VALUES (0);

--
-- Name: forgettoken_record; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.forgettoken_record (
    email character varying,
    send_time timestamp without time zone DEFAULT now()
);


--
-- Name: questions; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.questions (
    qid varchar NOT NULL,
    question character varying NOT NULL,
    answer varchar,
    competition varchar NOT NULL,
    round integer,
    send_date date,
    seq_id serial
);


--
-- Name: register; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.register ( 
    team_id serial,
    competition character varying NOT NULL,
    email character varying NOT NULL,
    register_time timestamp without time zone DEFAULT now(),
    status_code integer DEFAULT 0,
    revoke_time timestamp without time zone,
    code character(6),
    team_name character varying
);


--
-- Name: status; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.status (
    status_code integer NOT NULL,
    status_desc character varying NOT NULL
);

insert into public.status(status_code,status_desc)
values
(1,'register success'),
(903,'client server timeout'),
(200,'handler get answer success'),
(500, 'client server error'),
(900,'Request Error'),
(901,'Http Error'),
(902,'Connection Error'),
(904,'Wrong URL format'),
(905,'Invalid URL,url format should be http://'),
(906,'Value Error'),
(907,'Wrong URL format'),
(999,'Wrong Answer Format'),
(404,'URL NOT FOUND');

--
-- Name: tbrain_info; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.tbrain_info (
    team_name character varying NOT NULL,
    email character varying NOT NULL,
    team_leader_ind boolean,
    competition character varying
);


--
-- Name: users; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS    public.users (
    phone character(20) NOT NULL,
    email character varying NOT NULL,
    competition character varying NOT NULL,
    code character(6),
    create_dt timestamp without time zone DEFAULT now()
);


--
-- Name: verification; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.verification (
    team_id integer,
    api_url character varying,
    status_code_infer integer,
    verification_time timestamp without time zone,
    verification_id character varying,
    serial_id serial
);

--
-- Name: verification; Type: TABLE; Schema: public;
--

CREATE TABLE IF NOT EXISTS    public.generator_status (
    team_id integer,
    send_date timestamp without time zone,
    insert_question_status integer
);

--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (qid);


--
-- Name: register register_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.register
    ADD CONSTRAINT register_pkey PRIMARY KEY (team_id);


--
-- Name: status status_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.status
    ADD CONSTRAINT status_pkey PRIMARY KEY (status_code);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (competition, email);


--
-- Name: answers answers_qid_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT answers_qid_fkey FOREIGN KEY (qid) REFERENCES public.questions(qid);


--
-- Name: answers constraint_fk; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT constraint_fk FOREIGN KEY (team_id) REFERENCES public.register(team_id);



--
-- Name: answers constraint_fk2; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT constraint_fk2 FOREIGN KEY (status_code) REFERENCES public.status(status_code);




--
-- Name: register register_competition_fkey; Type: FK CONSTRAINT; Schema: public;
--

ALTER TABLE ONLY public.register
    ADD CONSTRAINT register_competition_fkey FOREIGN KEY (competition, email) REFERENCES public.users(competition, email);


--
-- Name: register register_status_code_fkey; Type: FK CONSTRAINT; Schema: public; 
--

ALTER TABLE ONLY public.register
    ADD CONSTRAINT register_status_code_fkey FOREIGN KEY (status_code) REFERENCES public.status(status_code);

ALTER TABLE public.verification ADD CONSTRAINT verification_status_code_infer_fkey FOREIGN KEY (status_code_infer) REFERENCES public.status(status_code);
