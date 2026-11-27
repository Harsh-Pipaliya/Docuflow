# Configuration

The Compose project publishes the Flask API at 127.0.0.1:8080. The emulator, worker and bootstrap communicate on its private network. EMULATOR_URL and FIRESTORE_EMULATOR_HOST route SDK calls to the cloud container. The application uses a local docuflow project and docuflow-uploads bucket.

The setup script generates a bcrypt DEMO_PASSWORD_HASH in .env. The username is demo. MAX_UPLOAD_BYTES defaults to 10485760, LOGIN_FAILURES_PER_MINUTE to 5, UPLOADS_PER_MINUTE to 10 and SESSION_IDLE_MINUTES to 30. Each opaque session cookie refers to a server-side SQLite record. FORCE_FAILURE_FILE_ID is empty by default; tests target one synthetic UUID in an isolated worker process. The API allows application/pdf only. The operational log uses fixed JSON fields.
