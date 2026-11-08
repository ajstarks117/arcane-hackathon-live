"""Durable documents for the single-process Render API."""
import os
import psycopg
from psycopg.types.json import Jsonb

def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=8)

def initialize():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS arcane_documents (name text PRIMARY KEY, value jsonb NOT NULL)")

def read(name, default):
    with connect() as db:
        row = db.execute("SELECT value FROM arcane_documents WHERE name = %s", (name,)).fetchone()
    return row[0] if row else default

def write(name, value):
    with connect() as db:
        db.execute("INSERT INTO arcane_documents VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET value = excluded.value", (name, Jsonb(value)))
