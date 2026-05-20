
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- ===============================
-- 1) Tabel modules
-- ===============================
CREATE TABLE modules (
  id           bigserial PRIMARY KEY,
  module_name  text NOT NULL,
  course_id    integer NOT NULL,
  course_name  text NOT NULL,
  ref_module_id integer NOT NULL,
  tenant_id    integer NOT NULL,
  created_at   timestamptz DEFAULT now()
);

-- ===============================
-- 2) Tabel chunks (relasi ke modules)
-- ===============================
CREATE TABLE chunks (
  id          bigserial PRIMARY KEY,
  module_id   bigint NOT NULL,
  chunk_text  text NOT NULL,
  tenant_id   integer NOT NULL,

  CONSTRAINT fk_chunks_module
    FOREIGN KEY (module_id)
    REFERENCES modules(id)
    ON DELETE CASCADE
);

-- ===============================
-- 3) Tabel tbl_vector (relasi ke chunks)
-- ===============================
CREATE TABLE tbl_vector (
  id         bigserial PRIMARY KEY,
  embedding  vector(3072) NOT NULL,
  chunk_id   bigint NOT NULL,
  tenant_id  integer NOT NULL,

  CONSTRAINT fk_vector_chunk
    FOREIGN KEY (chunk_id)
    REFERENCES chunks(id)
    ON DELETE CASCADE
);

-- ===============================
-- 4) Tabel module_annotations
-- ===============================
CREATE TABLE module_annotations (
  id           bigserial PRIMARY KEY,
  module_id    bigint NOT NULL,
  page_number  integer NOT NULL CHECK (page_number > 0),
  text         text NOT NULL,
  tenant_id    integer NOT NULL,

  CONSTRAINT fk_annotations_module
    FOREIGN KEY (module_id)
    REFERENCES modules(id)
    ON DELETE CASCADE
);

